import docker
from fabric.api import task, show, local, lcd, hide
from fabric.colors import red, green
from settings import containers, FABENV
from fabric.contrib.console import confirm
import socket
from os.path import join
from settings import all_project, yamlconfig
import time

client = docker.from_env()


# api 出现很大的问题, 改用命令行


@task
def start_redis(port, network='', version=''):
    if port:
        p = is_open(port='6379', p=False)
        if p:
            print(green('redis already start ...'))
            return False

    env = {
        'REDIS_PASS': 'wothing',
        'REDIS_DIR': '/data',
    }

    # localhost test
    ports = {}
    if port:
        ports = {'6379/tcp': 6379}

    print(green('start redis ...'))
    if not network:
        with show('stdout', 'stderr', 'debug'):
            cmd = 'docker run -d -ti -e REDIS_PASS=wothing -e REDIS_DIR=/data -p 127.0.0.1:80:8080 %s' \
                  % containers['redis']
            local(cmd)
            # container = client.containers.run(containers['redis'], detach=True, environment=env, ports=ports)
        # if not container.name:
        #     print(red('start redis faild!'))
        #     return
        print(green('redis complete!'))
        return 'new'
    else:
        if not version:
            print(red('need version'))
            return False

        with show('stdout', 'stderr', 'debug'):
            networks = [FABENV['bridge']]
            name = 'redis_' + version
            cmd = '''docker run -d -ti -e REDIS_PASS=wothing -e REDIS_DIR=/data \
                  --net=test --name=%s %s''' % (name, containers['redis'])
            local(cmd)
            # container = client.containers.run(containers['redis'], detach=True, environment=env, ports=ports, name=name,
            #                                   networks=networks)
            # if not container.name:
            #     print(red('start redis faild!'))
            #     return


@task
def start_pgsql(port, network='', version=''):
    if port:
        p = is_open(port='5432', p=False)
        if p:
            print(green('postgresql already start ...'))
            return 'old'

    env = {
        'POSTGRES_DB': 'butler',
        'POSTGRES_PASSWORD': '',
    }

    ports = {}
    if port:
        ports = {'5432/tcp': 5432}

    print(green('start postgresql ...'))
    if not network:
        with show('stdout', 'stderr', 'debug'):
            container = client.containers.run(containers['postgres'], detach=True, environment=env,
                                              ports=ports)
            if not container.name:
                print(red('start postgresql faild!'))
                return
            print(green('postgresql complete!'))
            return 'new'
    else:
        if not version:
            print(red('need version'))
            return

        with show('stdout', 'stderr', 'debug'):
            networks = [FABENV['bridge']]
            name = 'postgresql_' + version
            container = client.containers.run(containers['postgres'], detach=True, environment=env, name=name,
                                              ports=ports, networks=networks)
            if not container.name:
                print(red('start postgresql faild!'))
                return


@task
def start_etcd(port, network='', version=''):
    if port:
        p = is_open(port='2379', p=False)
        if p:
            print(green('etcd already start ...'))
            return 'old'

    env = {
    }

    ports = {}
    if port:
        ports = {'2379/tcp': 2379, '4001/tcp': 4001}

    print(green('start etcd ...'))
    if not network:
        c = client.containers.run(containers['etcd'], detach=True, environment=env, ports=ports)
        if c.status != 'created':
            print(red('start etcd faild!'))
            return
        print(green('etcd complete!'))
        return 'new'
    else:
        if not version:
            print(red('need version'))
            return
        networks = [FABENV['bridge']]
        name = 'etcd_' + version
        c = client.containers.run(containers['etcd'], detach=True, environment=env, ports=ports, networks=networks,
                                  name=name)
        if c.status != 'created':
            print(red('start etcd faild!'))
            return


@task
def docker_list():
    for container in client.containers.list():
        print(container.name)
        print(container.status)


@task
def clean_docker():
    """[SA] 停止所有的docker container"""
    for c in client.containers.list(all=True):
        print(green('clean container: %s' % c.name))
        if c.status == "exited":
            c = client.containers.get(c.id)
            c.remove()


@task
def stop_docker():
    for c in client.containers.list(all=True):
        print(green('stop container: %s' % c.name))
        cg = client.containers.get(c.id)
        cg.stop(timeout=100)


@task
def clean_docker():
    """[SA] 清除本地所有的docker container"""
    stop_docker()
    clean_docker()


@task
def clean_container_force():
    """[SA] 强制清除本地所有的docker container"""
    if confirm("clean all container .Continue anyway?"):
        local("docker stop $(docker ps -q -a)")
        local("docker rm $(docker ps -q -a )")


@task
def start_all(port=False):
    start_etcd(port=port)
    start_pgsql(port=port)
    start_redis(port=port)


@task
def test(count=10):
    c = client.containers.run(containers['redis'], detach=True, networks=['test'], network_mode='bridge')

    # nl = client.networks.list(names='test')
    # for n in nl:


@task
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


@task
def build_docker_image(micro, tag):
    if (not micro) or (not tag):
        print(red('you need micro name and version !'))
        return False

    p = join(FABENV['project'], 'linux_build')
    fname = micro + '-Dockerfile'
    tag = FABENV['registry'] + '/' + FABENV['project_name'] + '/' + micro + ':' + tag
    i = client.images.build(path=p, dockerfile=fname, tag=tag)
    if not i.tags:
        return False
    else:
        return True


@task
def project_test(version):
    """[local] 使用docker进行集成测试 example: fab project_test:0.1"""
    # network
    create_network(FABENV['bridge'], False)

    # build
    print(green('building test image ...'))
    p = join(FABENV['project'], 'linux_build')
    fname = 'test-Dockerfile'
    tag = 'test:latest'
    i = client.images.build(path=p, dockerfile=fname, tag=tag)

    if i.tags:
        # run
        networks = [FABENV['bridge']]
        database = "database=postgresql_" + version
        appway = "appway=appway_" + version
        env = ["TestEnv=CI", "CiTracer=other", database, appway]
        name = 'test_' + version
        client.containers.run(image="test:latest", detach=True, networks=networks, name=name, environment=env)


@task
def project_docker(version):
    """[local] 将所有的微服务用docker跑起来 fab project_test:0.1"""
    if not version:
        print(red('you need version !'))
        return

    nf = time.strftime("%m%d%H%M", time.localtime(time.time()))
    tag = version + '_' + nf
    for a in all_project():
        print(green('building %s ...' % a))
        b = build_docker_image(a, tag)
        if b:
            continue
        else:
            print(red('build image %s error!' % a))

    docker_run(version)


@task
def docker_run(version):
    # network
    create_network(FABENV['bridge'], False)
    # run
    networks = [FABENV['bridge']]

    for d in all_project():
        name = d + '-' + version
        print(green('running container %s ...' % name))
        image = FABENV['registry'] + '/' + FABENV['project_name'] + '/' + d + ':' + version
        client.containers.run(image=image, detach=True, networks=networks, name=name)


def create_network(network, p=True):
    if not network:
        print(red('you need network name !'))
        return

    n = client.networks.create(network, driver="bridge")
    if n.name:
        if p:
            print(green('create bridge network %s succeed!' % network))
        return True
    else:
        if p:
            print(green('create bridge network %s false!' % network))
        return False


def delete_netwrok(network, p=True):
    n = client.networks.list()
    for i in n:
        if i.name == network:
            if p:
                print(green('network %s removed!' % network))
            i.remove()


def network_exist(network, p=True):
    n = client.networks.list()
    for i in n:
        if i.name == network:
            if p:
                print(green('network %s exist!' % network))
                return True
    return False


@task
def push_image(micro, version):
    """[local] 推送镜像到阿里云 example: fab push_image:master,v1.1_03021623"""
    if (not micro) or (not version):
        print(green('need micro and version'))
        return
    repository = FABENV['registry'] + '/' + FABENV['project_name'] + '/' + micro
    print(client.images.push(repository=repository, tag=version))


@task
def clean_docker_version(version):
    """[local] 停止并删除指定版本的镜像 example: fab clean_docker_version:v1.1_03021630"""
    if not version:
        print(green('need version'))
        return
    try:
        local("docker stop $(docker ps -a  | grep '%s' | awk '{print $1}')" % version)
    except:
        local("docker rmi -f $(docker images -a | grep '%s' | awk '{print $3}')" % version)


@task
def postgresql_init(version):
    """[local] 初始化postgresql"""
    # init file
    f = open(join(yamlconfig['env']['project_path'], yamlconfig['prod']['build_path'], 'init_postgresql.sh'), 'w')
    psql = '`which psql` -h postgresql_' + version + ' -p 5432' + ' -U postgres' + ' -d ' + yamlconfig['env'][
        'project_name']
    exten_sql = '`which psql` -h postgresql_' + version + ' -p 5432' + ' -U postgres' + ' -d ' + yamlconfig['env'][
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

    cmd = cmd.format(sql_dir=yamlconfig['env']['sql_dir'], build_path=yamlconfig['prod']['build_path'],
                     project_path=yamlconfig['env']['project_path'], network_bridge=yamlconfig['env']['network_bridge'])

    with hide('running'):
        local(cmd)


@task
def etcd_init(version):
    """[local] 初始化 etcd"""
    keys = {'/butler/pgsql/host': 'postgresql_' + version,
            '/butler/pgsql/port': '5432',
            '/butler/pgsql/name': 'butler',
            '/butler/pgsql/user': 'postgres',
            '/butler/pgsql/password': '\'\'',
            '/butler/redis/host': 'redis_' + version,
            '/butler/redis/port': '6379',
            '/butler/redis/password': '\'\'',
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


@task
def nsq_init(version):
    """[local] 初始化 nsq"""