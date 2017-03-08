## define roledefs
from fabric.api import task

ROLEDEFS = {
    'dev': ['139.196.136.87'],
    'k8s': ['192.168.0.1', '192.168.0.2', '192.168.0.3'],
    'pg': ['192.168.0.5', '192.168.0.6'],
    'redis': ['192.168.0.8'],
    'nsq': ['192.168.0.8'],
    'es': ['192.168.0.1', '192.168.0.4'],
    'kibana': ['192.168.0.4'],
    'nginx': ['192.168.0.7'],
}


@task
def eeee():
    print('good')


@task
def xxxx():
    print("xxxx")


@task(default=True)
def full_deploy():
    pass
