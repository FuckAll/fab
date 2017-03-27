from fabric.api import task, local, hide
from fabric.colors import green
from fabric.contrib.console import confirm
from os.path import join
from settings import yamlconfig


@task
def clean_container_force():
    """[SA] 强制清除本地所有的docker container"""
    if confirm("clean all container .Continue anyway?"):
        local("docker stop $(docker ps -q -a)")
        local("docker rm $(docker ps -q -a )")


@task
def clean_docker_version(version):
    """[production] 停止并删除指定版本的镜像 example: fab clean_docker_version:v1.1_03021630"""
    if not version:
        print(green('need version'))
        return
    # try:
    local("docker stop $(docker ps -a  | grep '%s' | awk '{print $1}')" % version)
    local("docker rm -f $(docker ps -a | grep '%s' | awk '{print $1}')" % version)
    local("docker rmi -f $(docker images -a | grep '%s' | awk '{print $3}')" % version)
    # except:
    #     local("docker rmi -f $(docker images -a | grep '%s' | awk '{print $3}')" % version)


@task
def postgresql_init(version):
    """[production] 初始化postgresql"""
    # init file
    f = open(join(yamlconfig['project_path'], yamlconfig['prod']['build_path'], 'init_postgresql.sh'), 'w')
    psql = '`which psql` -h postgresql_' + version + ' -p 5432' + ' -U postgres' + ' -d ' + yamlconfig[
        'project_name']
    exten_sql = '`which psql` -h postgresql_' + version + ' -p 5432' + ' -U postgres' + ' -d ' + yamlconfig[
        'project_name'] + ' -c "CREATE EXTENSION IF NOT EXISTS "pgcrypto""'

    contant = '''#!/bin/sh
%s
all=`find sql -type f -iname "*.sql" | sort -t "/" -k 2,2`
for a in $all
do
%s -f $a
done
''' % (exten_sql, psql)
    f.write(contant)
    f.close()

    cmd = ''' docker run --rm -ti --net={network_bridge} \
     -v {sql_dir}:/sql/ \
     -v {project_path}/{build_path}/init_postgresql.sh:/init_postgresql.sh \
     daocloud.io/izgnod/postgres:latest sh init_postgresql.sh'''

    cmd = cmd.format(sql_dir=yamlconfig['sql_dir'], build_path=yamlconfig['prod']['build_path'],
                     project_path=yamlconfig['project_path'], network_bridge=yamlconfig['network_bridge'])

    with hide('running'):
        local(cmd)


@task
def etcd_init(version):
    """[production] 初始化 etcd"""
    keys = {'/butler/pgsql/host': 'postgresql_' + version,
            '/butler/pgsql/port': '5432',
            '/butler/pgsql/name': 'butler',
            '/butler/pgsql/user': 'postgres',
            '/butler/pgsql/password': '\'\'',
            '/butler/redis/host': 'redis_' + version,
            '/butler/redis/port': '6379',
            '/butler/redis/password': 'wothing',
            '/butler/nsqd/host': 'nsqd_' + version,
            '/butler/nsqd/port': '4150',
            '/butler/nsql/host': 'nsql_' + version,
            '/butler/nsql/port': '4161',
            '/butler/mediastore/mode': 'test',
            '/butler/wechat/web/appid': 'wxc3a713d594283b00',
            '/butler/wechat/web/appsecret': '66edd83a09789b1fb88535e3f14ae94c',
            '/butler/wechat/web/consult_url': 'http://butler.17mei.top/wp/butler',
            '/butler/wechat/web/auth_url': '\'https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&scope=snsapi_base&state=%s#wechat_redirect\''
            }

    for k in keys:
        cmd = 'docker exec -ti etcd_{version} etcdctl set {k} {v}'
        cmd = cmd.format(version=version, k=k, v=keys[k])
        with hide('running', 'stdout'):
            print(green('etcdctl set %s %s') % (k, keys[k]))
            local(cmd)
