from fabric.api import task, lcd, local, hide
from fabric.colors import green
from settings import FABENV
from os import listdir
from os.path import isdir, join

dockerfile = '''FROM daocloud.io/izgnod/alpine:latest
COPY %s /%s
CMD exec /%s -etcd $ETCD -h $HOSTNAME -p $P
'''

gateway_dockerfile = '''FROM daocloud.io/izgnod/alpine:latest
COPY %s /%s
COPY 17mei.crt /17mei.crt
COPY 17mei.key /17mei.key
CMD exec /%s -etcd $ETCD -h $HOSTNAME -p $P
'''
test_dockerfile = '''FROM daocloud.io/izgnod/alpine:latest
COPY test /test
CMD exec /test
'''

@task
def linux_build_prepare():
    with lcd(FABENV['project']):
        local('make idl ', capture=True)
        local('if [[ ! -d linux_build ]]; then mkdir ./linux_build; fi')


@task
def linux_build_all():
    with lcd(FABENV['project']):
        onlydir = [f for f in listdir(FABENV['project']) if isdir(join(FABENV['project'], f)) and f not in
                   FABENV['exclude']]
        for d in onlydir:
            if d == 'gateway':
                linux_build_gateway()
                create_gateway_dockerfile()
            else:
                linnux_build(d)
                create_micro_dockerfile(d)


@task
def linnux_build(micro='mall'):
    with hide('running', 'stdout'):
        print(green('build linux version %s service ...' % micro))
        with lcd(join(FABENV['project'], micro)):
            local('GOARCH=amd64 GOOS=linux CGO_ENABLED=0 go build -v -i -o %s' % join(FABENV['project'], 'linux_build',
                                                                                      micro))


@task
def linux_build_gateway():
    with hide('running', 'stdout'):
        print(green('build linux version appway and interway service ...'))
        with lcd(join(FABENV['project'], 'gateway', 'appway')):
            local('GOARCH=amd64 GOOS=linux CGO_ENABLED=0 go build -v -i -o %s' % join(FABENV['project'], 'linux_build',
                                                                                      'appway'))
        with lcd(join(FABENV['project'], 'gateway', 'interway')):
            local('GOARCH=amd64 GOOS=linux CGO_ENABLED=0 go build -v -i -o %s' % join(FABENV['project'], 'linux_build',
                                                                                      'interway'))


@task
def create_micro_dockerfile(micro='mall'):
    with hide('running', 'stdout'):
        content = dockerfile % (micro, micro, micro)
        f = open(join(FABENV['project'], 'linux_build', micro + '-Dockerfile'), 'w')
        f.write(content)
        f.close()


@task
def create_gateway_dockerfile():
    gateway = ['appway', 'interway']
    with hide('running', 'stdout'):
        for g in gateway:
            content = gateway_dockerfile % (g, g, g)
            f = open(join(FABENV['project'], 'linux_build', g + '-Dockerfile'), 'w')
            f.write(content)
            f.close()


@task
def linux_build_test():
    with hide('running', 'stdout'):
        print(green('build linux version test ...'))
        with lcd(FABENV['test_dir']):
            local('GOARCH=amd64 GOOS=linux CGO_ENABLED=0 go test -c -o %s' % join(FABENV['project'], 'linux_build',
                                                                                  'test'))
            f = open(join(FABENV['project'], 'linux_build', 'test-Dockerfile'), 'w')
            f.write(test_dockerfile)
            f.close()
