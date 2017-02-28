from fabric.api import task, hosts, run, cd, lcd, settings, hide, local
from site_config import ROLEDEFS
from settings import *
import os
from fabric.colors import red, green

import asyncio
import asyncpg

import etcd

@task
@hosts(ROLEDEFS['dev'])
def dev_nginx():
    git_pull()


# git_pull nginx
def git_pull():
    code_dir = os.path.join(BASE_PREPARE_DIR + '17mei-ops')
    if run("test -d %s" % code_dir).failed:
        run("git clone %s" % MEI_OPS)
    with cd(code_dir):
        run('git pull')
        run("git log -1 |grep commit|awk '{print $2}' > .revision")


# restart nginx
def restart_nginx():
    run('/usr/sbin/nginx -c /etc/nginx/nginx.conf')


# init postgresql
@task
def init_postgresql():
    pg_extension()
    with lcd('sql'):
        path = local('pwd', capture=True)
        for root, dirs, filenames in os.walk(path):
            for f in filenames:
                if ".sql" in f:
                    sql = root + '/' + f
                    print(green('execute : %s' % sql))
                    async def run():
                        conn = await asyncpg.connect(user='postgres', password='wothing', database='butler', host='127.0.0.1')
                        await conn.execute(open(sql).read())
                        await conn.close()

                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(run())


@task
def pg_extension():
    extensions = ['CREATE EXTENSION IF NOT EXISTS "pgcrypto"']

    async def run():
        conn = await asyncpg.connect(user='postgres', password='wothing', database='butler', host='127.0.0.1')
        for e in extensions:
            await conn.execute(e)
        await conn.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@task
def init_etcd():
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
    #
    # print(client.read('/nodes/n2').value)


@task
def get_key():
    client = etcd.Client(host='127.0.0.1', port=2379)
    print(client.read('/butler/pgsql/host').value)