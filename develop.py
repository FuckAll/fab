from fabric.api import task, hosts, run, cd, lcd, hide, local
from site_config import ROLEDEFS
from settings import BASE_PREPARE_DIR, MEI_OPS, FABENV
from os import listdir, walk
from os.path import isfile, join, isdir
from fabric.colors import red, green
from hashlib import md5
from time import sleep
from docker_local import start_pgsql, start_etcd, start_redis
import asyncio
import asyncpg
import etcd


@task
@hosts(ROLEDEFS['dev'])
def dev_nginx():
    git_pull()


# git_pull nginx
def git_pull():
    code_dir = join(BASE_PREPARE_DIR + '17mei-ops')
    if run("test -d %s" % code_dir).failed:
        run("git clone %s" % MEI_OPS)
    with cd(code_dir):
        run('git pull')
        run("git log -1 |grep commit|awk '{print $2}' > .revision")


# restart nginx
def restart_nginx():
    run('/usr/sbin/nginx -c /etc/nginx/nginx.conf')


@task
def init_postgresql():
    """ [local] 初始化本地数据库（导入表等）"""
    pg_extension()
    with lcd(join(FABENV['project'], 'sql')):
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


@task
def pg_extension():
    """ [local] 添加数据库扩展"""
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
def init_etcd():
    """ [local] 初始化etcd keys"""
    client = etcd.Client(host='127.0.0.1', port=2379)
    keys = {'/butler/pgsql/host': '127.0.0.1',
            '/butler/pgsql/port': '5432',
            '/butler/pgsql/name': 'butler',
            '/butler/pgsql/user': 'postgres',
            '/butler/pgsql/password': 'wothing',
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
def get_key():
    client = etcd.Client(host='127.0.0.1', port=2379)
    print(client.read('/butler/pgsql/host').value)


@task
def start_all_micro():
    """ [local] 启动所有的微服务"""

    with lcd(FABENV['project']):
        onlydir = [f for f in listdir(FABENV['project']) if isdir(join(FABENV['project'], f)) and f not in
                   FABENV['exclude']]
        for d in onlydir:
            if d == 'gateway':
                build_gateway()
            else:
                build(d)


@task
def stop_all_micro():
    """ [local] 停止所有的微服务"""
    print(green('stop all micro service ...'))
    with hide('running'):
        local("ps -ef | grep build/ | grep -v grep  | awk '{print $2}' | xargs kill -9", capture=True)


@task
def force_rebuild_micro():
    with hide('running'):
        with lcd(FABENV['project']):
            local('rm -rf ./build')
        start_all_micro()


@task
def build_gateway():
    """ [local] 构建并且重启gateway"""
    with hide('running'):
        with lcd(FABENV['project']):
            local('if [[ ! -d build ]]; then mkdir ./build; fi')
            local('if [[ ! -d logs ]]; then mkdir ./logs; fi')

            c = dir_change('gateway')
            if c:
                # build
                print(green('build && restart appway and interway micro service...'))
                with lcd(join(FABENV['project'], 'gateway/appway')):
                    local('go build -v -i -o %s' % join(FABENV['project'], 'build', 'appway'))
                with lcd(join(FABENV['project'], 'gateway/interway')):
                    local('go build -v -i -o %s' % join(FABENV['project'], 'build', 'interway'))

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


@task
def build(micro='mall'):
    """ [local] 构建并且重启micro example: fab build:mall"""
    with hide('running'):
        with lcd(FABENV['project']):
            local('if [[ ! -d build ]]; then mkdir ./build; fi')
            local('if [[ ! -d logs ]]; then mkdir ./logs; fi')

        if not micro:
            print(red("need micro's name to build"))

        # build
        c = dir_change(micro)
        if c:
            print(green('build and restart %s micro service...' % micro))
            with lcd(join(FABENV['project'], micro)):
                local('go build -v -i -o %s' % join(FABENV['project'], 'build', micro))
            micro_restart(micro)

        # check
        ck = micro_status(micro, False)
        if not ck:
            micro_start(micro)


@task
def micro_restart(micro='mall'):
    """ [local] 重启micro example: fab micro_restart:mall"""
    with hide('running'):
        local("ps -ef | grep build/%s | grep -v grep  | awk '{print $2}' | xargs kill -9" % micro, capture=True)
        with lcd(FABENV['project']):
            local('nohup build/%s >> logs/debug.log 2>&1 &' % micro)


@task
def micro_start(micro='mall'):
    """ [local] 启动micro example: fab micro_start:mall"""
    with hide('running'):
        with lcd(FABENV['project']):
            local('nohup build/%s >> logs/debug.log 2>&1 &' % micro)


@task
def micro_status(micro='mall', p=True):
    """ [local] 查看micro运行状态 example: fab micro_status:mall"""
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
    with lcd(FABENV['project']):
        md5file = join(FABENV['project'], 'build/%s.md5' % micro)
        microdir = join(FABENV['project'], micro)

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


@task
def start_workspace():
    # 1. 启动数据库
    if not start_pgsql(True):
        sleep(10)
        init_postgresql()

    # 2. 启动etcd

    if not start_etcd(True):
        sleep(3)
        init_etcd()
    # 3. 启动redis
    start_redis(True)

    # 4. 启动nsq

    # 4. 启动业务
    start_all_micro()
