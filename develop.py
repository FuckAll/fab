from fabric.api import task, lcd, hide, local
from settings import yamlconfig
from os import listdir, walk
from os.path import isfile, join, isdir
from fabric.colors import red, green
from hashlib import md5
import asyncio
import asyncpg
import etcd
import socket


@task
def develop_init_postgresql():
    """ [develop] 初始化本地数据库（导入表等）"""
    pg_extension()
    with lcd(join(yamlconfig['project_path'], 'sql')):
        with hide('running'):
            path = local('pwd', capture=True)
            for root, dirs, filenames in walk(path):
                for f in filenames:
                    if ".sql" in f:
                        sql = root + '/' + f
                        print(green('execute : %s' % sql))

                        async def run():
                            conn = await asyncpg.connect(user='postgres', password='wothing', database='butler',
                                                         host='127.0.0.1', port='5432')
                            await conn.execute(open(sql).read())
                            await conn.close()

                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(run())


def pg_extension():
    """ [develop] 添加数据库扩展"""
    extensions = ['CREATE EXTENSION IF NOT EXISTS "pgcrypto"']

    async def run():
        conn = await asyncpg.connect(user='postgres', password='wothing', database='butler', host='127.0.0.1',
                                     port='5432')
        for e in extensions:
            await conn.execute(e)
        await conn.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@task
def develop_init_etcd():
    """ [develop] 初始化etcd keys"""
    client = etcd.Client(host='127.0.0.1', port=2379)
    keys = {'/butler/pgsql/host': '127.0.0.1',
            '/butler/pgsql/port': '5432',
            '/butler/pgsql/name': 'butler',
            '/butler/pgsql/user': 'postgres',
            '/butler/pgsql/password': '',
            '/butler/redis/host': '127.0.0.1',
            '/butler/redis/port': '6379',
            '/butler/redis/password': 'wothing',
            '/butler/mediastore/mode': 'test',
            '/butler/wechat/web/appid': 'wxc3a713d594283b00',
            '/butler/wechat/web/appsecret': '66edd83a09789b1fb88535e3f14ae94c',
            '/butler/wechat/web/consult_url': 'http://butler.17mei.top/wp/butler',
            '/butler/wechat/web/auth_url': 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&scope=snsapi_base&state=%s#wechat_redirect'
            }

    for key in keys:
        print(green("set key: %s value: %s" % (key, keys[key])))
        client.write(key, keys[key])


@task
def start_all_micro():
    """ [develop] 启动所有的微服务"""
    before_build()
    with lcd(yamlconfig['project_path']):
        onlydir = [f for f in listdir(yamlconfig['project_path']) if
                   isdir(join(yamlconfig['project_path'], f)) and f not in
                   yamlconfig['dev']['build_exclude']]
        for d in onlydir:
            if d == 'gateway':
                build_gateway()
            else:
                build(d)
    # iterm_applescript()


def stop_all_micro():
    """ [develop] 停止所有的微服务"""
    print(green('stop all micro service ...'))
    with hide('running'):
        # local("ps -ef | grep build/ | grep -v grep  | awk '{print $2}' | xargs kill -9", capture=True)
        local("ps -ef | grep build/ | grep -v grep  | awk '{print $2}' | xargs kill", capture=True)


@task
def force_rebuild_micro():
    """[develop] 强制重新build并且启动"""
    with hide('running'):
        with lcd(yamlconfig['project_path']):
            local('rm -rf ./build')
        start_all_micro()


def build_gateway():
    """ [develop] 构建并且重启gateway"""
    with hide('running'):
        with lcd(yamlconfig['project_path']):
            local('if [[ ! -d build ]]; then mkdir ./build; fi')
            local('if [[ ! -d logs ]]; then mkdir ./logs; fi')

            c = dir_change('gateway')
            if c:
                # build
                print(green('build && restart appway and interway micro service...'))
                with lcd(join(yamlconfig['project_path'], 'gateway/appway')):
                    local('go build -v -i -o %s' % join(yamlconfig['project_path'], 'build', 'appway'))
                with lcd(join(yamlconfig['project_path'], 'gateway/interway')):
                    local('go build -v -i -o %s' % join(yamlconfig['project_path'], 'build', 'interway'))

                # restart
                micro_restart('appway')
                micro_restart('interway')

            else:
                s = micro_status('appway', False)
                if not s:
                    micro_start('appway')

                s = micro_status('interway', False)
                if not s:
                    micro_restart('interway')


def build(micro='mall'):
    """ [develop] 构建并且重启micro example: fab build:mall"""
    with hide('running'):
        with lcd(yamlconfig['project_path']):
            local('if [[ ! -d build ]]; then mkdir ./build; fi')
            local('if [[ ! -d logs ]]; then mkdir ./logs; fi')

        if not micro:
            print(red("need micro's name to build"))

        # build
        c = dir_change(micro)
        if c:
            print(green('build and restart %s micro service...' % micro))
            with lcd(join(yamlconfig['project_path'], micro)):
                local('go build -v -i -o %s' % join(yamlconfig['project_path'], 'build', micro))
            micro_restart(micro)

        # check
        ck = micro_status(micro, False)
        if not ck:
            micro_start(micro)


def micro_restart(micro='mall'):
    """ [develop] 重启micro example: fab micro_restart:mall"""
    with hide('running'):
        local("ps -ef | grep build/%s | grep -v grep  | awk '{print $2}' | xargs kill -9" % micro, capture=True)
        with lcd(yamlconfig['project_path']):
            local('nohup build/%s >> logs/debug.log 2>&1 &' % micro)


def micro_start(micro='mall'):
    """ [develop] 启动micro example: fab micro_start:mall"""
    with hide('running'):
        with lcd(yamlconfig['project_path']):
            local('nohup build/%s >> logs/debug.log 2>&1 &' % micro)


def micro_status(micro='mall', p=True):
    """ [develop] 查看micro运行状态 example: fab micro_status:mall"""
    with hide('running'):
        r = local("ps -ef | grep build/%s | grep -v grep  | awk '{print $2}'" % micro, capture=True)
        if r:
            if p:
                print(green('micro %s already running.' % micro))
            return True
        else:
            if p:
                print(green('micro %s stopped.' % micro))
            return False


def dir_change(micro='mall'):
    with lcd(yamlconfig['project_path']):
        md5file = join(yamlconfig['project_path'], 'build/%s.md5' % micro)
        microdir = join(yamlconfig['project_path'], micro)

        if isfile(md5file):
            f = open(md5file, 'r')
            before_md5 = f.read()
            f.close()

            after_md5 = ''
            for root, subdirs, files in walk(microdir):
                for file in files:
                    filefullpath = join(root, file)

                    m = md5forfile(filefullpath)
                    after_md5 = after_md5 + filefullpath + ' ' + m + '\n'

            if before_md5 == after_md5:
                return False
            else:
                f = open(md5file, 'w')
                f.write(after_md5)
                return True
        else:
            f = open(md5file, 'w')
            after_md5 = ''
            for root, subdirs, files in walk(microdir):
                for file in files:
                    filefullpath = join(root, file)

                    m = md5forfile(filefullpath)
                    after_md5 = after_md5 + filefullpath + ' ' + m + '\n'
            f.write(after_md5)
            return True


def md5forfile(file):
    m = md5()
    a_file = open(file, 'rb')
    m.update(a_file.read())
    a_file.close()
    return m.hexdigest()


def develop_postgresql():
    cmd = yamlconfig['dev']['postgresql']['cmd']
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['dev']['postgresql']) and yamlconfig['dev']['postgresql']['init']:
        with hide('running'):
            local(yamlconfig['dev']['postgresql']['init'])


def develop_etcd():
    cmd = yamlconfig['dev']['etcd']['cmd']
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['dev']['etcd']) and yamlconfig['dev']['etcd']['init']:
        with hide('running'):
            local(yamlconfig['dev']['etcd']['init'])


def develop_redis():
    cmd = yamlconfig['dev']['redis']['cmd']
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['dev']['redis']) and yamlconfig['dev']['redis']['init']:
        with hide('running'):
            local(yamlconfig['dev']['redis']['init'])


@task
def develop_nsq():
    cmd = yamlconfig['dev']['nsqd']['cmd']
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['dev']['nsqd']) and yamlconfig['dev']['nsqd']['init']:
        with hide('running'):
            local(yamlconfig['dev']['nsqd']['init'])

    cmd = yamlconfig['dev']['nsql']['cmd']
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['dev']['nsql']) and yamlconfig['dev']['nsql']['init']:
        with hide('running'):
            local(yamlconfig['dev']['nsql']['init'])


def is_open(port, ip='127.0.0.1', p=True):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        if p:
            print('%s is open' % port)
        return True
    except:
        if p:
            print('%s is down' % port)
        return False


def before_build():
    with lcd(yamlconfig['project_path']):
        if 'before_build' in yamlconfig['dev'] and yamlconfig['dev']['before_build']:
            local(yamlconfig['dev']['before_build'])


@task
def start_workspace():
    """ [develop] 启动工作环境 example: fab start_workspace """
    if is_open(5432, ip='127.0.0.1', p=False):
        local('docker stop develop_postgresql')
        local('docker rm develop_postgresql')
        develop_postgresql()
    else:
        develop_postgresql()

    if is_open(6379, ip='127.0.0.1', p=False):
        local('docker stop develop_redis')
        local('docker rm develop_redis')
        develop_redis()
    else:
        develop_redis()

    if is_open(2379, ip='127.0.0.1', p=False):
        local('docker stop develop_etcd')
        local('docker rm develop_etcd')
        develop_etcd()
    else:
        develop_etcd()

    if is_open(4150, ip='127.0.0.1', p=False):
        local('docker stop develop_nsqd')
        local('docker stop develop_nsql')
        local('docker rm develop_nsqd')
        local('docker rm develop_nsql')
        develop_nsq()
    else:
        develop_nsq()

    # 4. 启动业务
    start_all_micro()

    # 5. iterm
    # iterm_applescript()


def iterm_applescript():
    cmd = """
    osascript \
            -e 'tell application "iTerm"'\
            -e 'set cmd to "tail -f %s"' \
            -e 'set len to count of sessions of current tab of current window' \
            -e 'if len ≤ 1 then' \
            -e 'tell current session of current tab of current window' \
            -e 'split horizontally with default profile command cmd' \
            -e 'end tell' \
            -e 'else' \
            -e 'tell session 2 of current tab of current window' \
            -e 'close' \
            -e 'end tell' \
            -e 'tell current session of current tab of current window' \
            -e 'split horizontally with default profile command cmd' \
            -e 'end tell' \
            -e 'end if' \
            -e 'end tell' \
        """ % join(yamlconfig['project_path'], 'logs', 'debug.log')
    with hide('running', 'stdout'):
        local(cmd)