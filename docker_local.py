import docker
from fabric.api import task, show, local
from fabric.colors import red, green
from settings import containers, FABENV
from fabric.contrib.console import confirm
import socket
from os.path import join


client = docker.from_env()


@task
def start_redis(port=False):
    p = is_open(port='6379', p=False)
    if p:
        print(green('redis already start ...'))
        return True

    env = {
        'REDIS_PASS': 'wothing',
        'REDIS_DIR': '/data',
    }

    # localhost test
    ports = {}
    if port:
        ports = {'6379/tcp': 6379}

    print(green('start redis ...'))
    with show('stdout', 'stderr', 'debug'):
        container = client.containers.run(containers['redis'], detach=True, environment=env, ports=ports)
    if container.name == '':
        print(red('start redis faild!'))
    print(green('redis complete!'))
    return True


@task
def start_pgsql(port=False):
    p = is_open(port='5432', p=False)
    if p:
        print(green('postgresql already start ...'))
        return True

    env = {
        'POSTGRES_DB': 'butler',
        'POSTGRES_PASSWORD': '',
    }

    ports = {}
    if port:
        ports = {'5432/tcp': 5432}

    print(green('start postgresql ...'))
    with show('stdout', 'stderr', 'debug'):
        container = client.containers.run(containers['postgres'], detach=True, environment=env,
                                          ports=ports)
    if container.name == '':
        print(red('start postgresql faild!'))


@task
def start_etcd(port=False):
    p = is_open(port='2379', p=False)
    if p:
        print(green('etcd already start ...'))
        return True

    env = {
    }

    ports = {}
    if port:
        ports = {'2379/tcp': 2379, '4001/tcp': 4001}

    print(green('start etcd ...'))
    c = client.containers.run(containers['etcd'], detach=True, environment=env, ports=ports)
    if c.status != 'created':
        print(red('start etcd faild!'))
    return True


# @task
# def start_nsq(port=False):
#     # docker
#     # run - -name
#     # nsqd - p
#     # 4150: 4150 - p
#     # 4151: 4151 \
#     #         nsqio / nsq / nsqd \
#     #         - -broadcast - address = 172.17
#     # .42
#     # .1 \
#     # - -lookupd - tcp - address = 172.17
#     # .42
#     # .1: 4160
#
#     command = "/nsqd"
#     ports = {}
#     if port:
#         ports = {'4150/tcp': 4150, '4151/tcp': 4151}
#
#     c = client.containers.run(containers['etcd'], detach=True, environment=env, ports=ports)

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
    for x in range(20):
        start_etcd()


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
def build_docker_image(micro='mall'):
    p = join(FABENV['project'], 'linux_build')
    fname = micro + '-Dockerfile'
    # TODO 这个地方要做一些准备, 例如标签如何打，如何统一命名等
    print(client.images.build(path=p, dockerfile=fname, tag='test:lates'))


@task
def create_etcd(port=False):
    p = is_open(port='2379', p=False)
    if p:
        print(green('etcd already start ...'))
        return True

    env = {
    }

    ports = {}
    if port:
        ports = {'2379/tcp': 2379, '4001/tcp': 4001}

    print(green('start etcd ...'))
    c = client.containers.create(containers['etcd'], detach=True, environment=env, ports=ports)
    print(c.stats)
    # c.i    # c = client.containers.run(containers['etcd'], detach=True, environment=env, ports=ports)
    # if c.status != 'created':
    #     print(red('start etcd faild!'))
    # return True



