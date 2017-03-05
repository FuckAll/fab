from fabric.api import task, lcd, local, hide,abort
from fabric.colors import green
from settings import FABENV, yamlconfig
from os import listdir
from os.path import isdir, join
import time

dockerfile = '''FROM daocloud.io/izgnod/alpine:latest
COPY %s /%s
CMD exec /%s -etcd $ETCD -h $HOSTNAME -p $P
'''

gateway_dockerfile = '''FROM daocloud.io/izgnod/alpine:latest
COPY %s /%s
CMD exec /%s -etcd $ETCD -h $HOSTNAME -p $P
'''

# COPY 17mei.crt /17mei.crt
# COPY 17mei.key /17mei.key
test_dockerfile = '''FROM daocloud.io/izgnod/alpine:latest
COPY test /test
CMD exec /test
'''


# meicrt = """
# -----BEGIN PUBLIC KEY-----
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmr3/mmSIB20U2dVDx0XN
# VERFNsGeP7ZpumLGjbMPnTURG5aevvEYd/CHIQG1swVUeV7kRhbYEo4JYZ1sz3TT
# AbAPYj/1cV/7lbPkn4j0glZuv5R5k1OX9T96Q6lEEkdapgGvfT3A+BBAgXzROdzX
# EGCHj6IPq0tIEvWCOvy9FEAD7uMpueF2T9xbyoiYpQHBObZWXe0OasXrX9V1YvVp
# QcepnBU1suHOW+3zM3MUhcr5Fh6K42jvOKGxXmqWdtglLzmopiraiq59Ay8bMLIe
# MNkqlywv0Oia4/EW5py2cixhqd4ur0k186gWm/Hnk3C0HCBaj6H0cb4zNCCnVXGY
# oQIDAQAB
# -----END PUBLIC KEY-----
# """
# meikey = """
# """

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
def create_micro_dockerfile(*args):
    for a in args:
        with hide('running', 'stdout'):
            if a in ['appway', 'interway', 'liveway']:
                content = gateway_dockerfile % (a, a, a)
            else:
                content = dockerfile % (a, a, a)
            dfile = join(yamlconfig['env']['project_path'], yamlconfig['prod']['build_path'],
                         a + yamlconfig['prod']['image']['extensions'])
            f = open(dfile, 'w')
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


@task
def build_test():
    # print(yamlconfig)
    with hide('running'):
        for cmd in yamlconfig['prod']['build']:
            with lcd(yamlconfig['env']['project_path']):
                local(cmd)


@task
def dockerfile_test():
    with hide('running'):
        for cmd in yamlconfig['prod']['image']['dockerfile']:
            local(cmd)


@task
def build_image_test(version):
    for cmd in yamlconfig['prod']['image']['build']:
        if ('{repo}' in cmd) and ('{version}' in cmd) and ('{dockerfile_extensions}' in cmd):
            cmd = cmd.format(repo=yamlconfig['env']['repo'],
                             version=version,
                             dockerfile_extensions=yamlconfig['env']['dockerfile_extensions'])

        else:
            abort('need {repo} {version} {dockerfile_extensions}')
            return

        with lcd(join(yamlconfig['env']['project_path'], yamlconfig['prod']['build_path'])):
            local(cmd)


@task
def remove_image_test(version):
    for cmd in yamlconfig['prod']['image']['remove']:
        if '{version}' in cmd:
            cmd = cmd.format(version=version)
        else:
            abort('need {version}')
        with hide('running'):
            local(cmd)



@task
def container_run_test(version):
    for cmd in yamlconfig['prod']['container']['run']['cmd']:
        if ('{network_bridge}' in cmd) and ('{version}' in cmd) and ('{repo}' in cmd):
            cmd = cmd.format(repo=yamlconfig['env']['repo'],
                             version=version,
                             network_bridge=yamlconfig['env']['network_bridge'])
        else:
            abort('need {repo} {version} {network_bridge}')
        local(cmd)


@task
def container_stop_test(version):
    for cmd in yamlconfig['prod']['container']['stop']['cmd']:
        if '{version}' in cmd:
            cmd = cmd.format(version=version)
            # print(cmd)
        else:
            abort('need {version}')
        with hide('running'):
            local(cmd)

