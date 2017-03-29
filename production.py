from fabric.api import task, lcd, local, hide, abort
from fabric.colors import green
from settings import yamlconfig
from os.path import join
import time

dockerfile = '''FROM daocloud.io/izgnod/alpine:latest
COPY %s /%s
CMD exec /%s -etcd $ETCD -h $HOSTNAME -p $P
'''

gateway_dockerfile = '''FROM daocloud.io/izgnod/alpine:latest
COPY %s /%s
CMD exec /%s -etcd $ETCD -h $HOSTNAME -p $P
'''


@task
def create_micro_dockerfile(*args):
    for a in args:
        with hide('running', 'stdout'):
            if a in ['appway', 'interway', 'liveway']:
                content = gateway_dockerfile % (a, a, a)
            else:
                content = dockerfile % (a, a, a)
            dfile = join(yamlconfig['project_path'], yamlconfig['prod']['build_path'],
                         a + yamlconfig['dockerfile_extensions'])
            f = open(dfile, 'w')
            f.write(content)
            f.close()


def prod_build():
    with hide('running'):
        for cmd in yamlconfig['prod']['build']:
            with lcd(yamlconfig['project_path']):
                local(cmd)


def prod_dockerfile():
    with hide('running'):
        for cmd in yamlconfig['prod']['image']['dockerfile']['cmd']:
            local(cmd)


def prod_build_image(version):
    for cmd in yamlconfig['prod']['image']['build']:
        if ('{repo}' in cmd) and ('{version}' in cmd) and ('{dockerfile_extensions}' in cmd):
            cmd = cmd.format(repo=yamlconfig['repo'],
                             version=version,
                             dockerfile_extensions=yamlconfig['dockerfile_extensions'])

        else:
            abort('need {repo} {version} {dockerfile_extensions}')
            return

        with lcd(join(yamlconfig['project_path'], yamlconfig['prod']['build_path'])):
            local(cmd)


@task
def prod_remove_image(version):
    """[production] 删除镜像 例如：fab prod_remove_image:03271807"""
    for cmd in yamlconfig['prod']['image']['remove']:
        if '{version}' in cmd:
            cmd = cmd.format(version=version, print='{print $3}')
        else:
            abort('need {version}')
        with hide('running'):
            # print(cmd)
            local(cmd)


@task
def prod_push_image(version):
    """[production] Push Image To Aliyun 例如：fab prod_remove_image:03271807"""
    for cmd in yamlconfig['prod']['image']['push']:
        if ('{version}' in cmd) and ('{repo}' in cmd):
            cmd = cmd.format(repo=yamlconfig['repo'],
                             version=version)
            print(cmd)
        else:
            abort('need {repo} {version}')
        with hide('running'):
            local(cmd)


@task
def prod_push_image_one(name='', version=''):
    if (not name) or (not version):
        abort('need name and version')
    local('docker push ' + yamlconfig['repo'] + name + ':' + version)


def prod_container_run(version):
    for cmd in yamlconfig['prod']['container']['run']['cmd']:
        if ('{network_bridge}' in cmd) and ('{version}' in cmd) and ('{repo}' in cmd):
            cmd = cmd.format(repo=yamlconfig['repo'],
                             version=version,
                             network_bridge=yamlconfig['network_bridge'])
        else:
            abort('need {repo} {version} {network_bridge}')
        local(cmd)


def prod_container_stop(version):
    for cmd in yamlconfig['prod']['container']['stop']['cmd']:
        if '{version}' in cmd:
            cmd = cmd.format(version=version)
        else:
            abort('need {version}')
        with hide('running'):
            local(cmd)


def prod_start_postgresql(version):
    cmd = yamlconfig['prod']['postgresql']['cmd']
    if ('{network_bridge}' in cmd) and ('{version}' in cmd):
        cmd = cmd.format(version=version, network_bridge=yamlconfig['network_bridge'])
    else:
        abort('need {version} {network_bridge}')
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['prod']['postgresql']) and yamlconfig['prod']['postgresql']['init']:
        with hide('running'):
            if '{version}' in yamlconfig['prod']['postgresql']['init']:
                local((yamlconfig['prod']['postgresql']['init']).format(version=version))


def prod_start_redis(version):
    cmd = yamlconfig['prod']['redis']['cmd']
    if ('{network_bridge}' in cmd) and ('{version}' in cmd):
        cmd = cmd.format(version=version, network_bridge=yamlconfig['network_bridge'])
    else:
        abort('need {version} {network_bridge}')
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['prod']['redis']) and yamlconfig['prod']['redis']['init']:
        local(yamlconfig['prod']['postgresql']['init'])


def prod_start_etcd(version):
    cmd = yamlconfig['prod']['etcd']['cmd']
    if ('{network_bridge}' in cmd) and ('{version}' in cmd):
        cmd = cmd.format(version=version, network_bridge=yamlconfig['network_bridge'])
    else:
        abort('need {version} {network_bridge}')
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['prod']['etcd']) and yamlconfig['prod']['etcd']['init']:
        local((yamlconfig['prod']['etcd']['init']).format(version=version))


@task
def prod_start_nsq(version):
    # nsqd
    cmd = yamlconfig['prod']['nsqd']['cmd']
    if ('{version}' in cmd) and ('{network_bridge}' in cmd):
        cmd = cmd.format(version=version, network_bridge=yamlconfig['network_bridge'])
    else:
        abort('need {version} {network_bridge}')

    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['prod']['nsqd']) and yamlconfig['prod']['nsqd']['init']:
        local((yamlconfig['prod']['nsqd']['init']).format(version=version))

    # nsql
    cmd = yamlconfig['prod']['nsql']['cmd']
    if ('{version}' in cmd) and ('{network_bridge}' in cmd):
        cmd = cmd.format(version=version, network_bridge=yamlconfig['network_bridge'])
    else:
        abort('need {version} {network_bridge}')

    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['prod']['nsql']) and yamlconfig['prod']['nsql']['init']:
        local((yamlconfig['prod']['nsql']['init']).format(version=version))


@task
def prod_test(version):
    """[production] 测试 例如：fab prod_test:03271807"""
    with lcd(yamlconfig['project_path']):
        for cmd in yamlconfig['prod']['test']['cmd']:
            if ('{project_path}' in cmd) and ('{build_path}' in cmd) and ('{version}' not in cmd):
                cmd = cmd.format(project_path=yamlconfig['project_path'],
                                 build_path=yamlconfig['prod']['build_path'])
                local(cmd)
            if ('{project_path}' in cmd) and ('{build_path}' in cmd) and ('{version}' in cmd) and (
                        '{network_bridge}' in cmd):
                cmd = cmd.format(project_path=yamlconfig['project_path'],
                                 build_path=yamlconfig['prod']['build_path'], version=version,
                                 network_bridge=yamlconfig['network_bridge'])
                local(cmd)


def prod_before_build():
    with lcd(yamlconfig['project_path']):
        if 'before_build' in yamlconfig['prod'] and yamlconfig['prod']['before_build']:
            local(yamlconfig['prod']['before_build'])


@task
def all_one(version='',push=''):
    """ [production] 编译，测试，提交"""
    if not version:
        version = time.strftime(yamlconfig['version'], time.localtime(time.time()))

    print(green('your version is %s !' % version))

    # before build
    print(green('git pull && make idl ....'))
    prod_before_build()

    # start base
    print(green('start postgresql ....'))
    prod_start_postgresql(version)
    print(green('start nsqd and nsqdl ....'))
    prod_start_nsq(version)
    print(green('start redis ....'))
    prod_start_redis(version)
    print(green('start etcd ....'))
    prod_start_etcd(version)

    # build image and run
    # docker file
    print(green('create dockerfile ....'))
    prod_dockerfile()

    # docker build
    print(green('start build micro ....'))
    prod_build()

    # docker image
    print(green('start build imiage ....'))
    prod_build_image(version)

    # docker run
    print(green('start container ....'))
    prod_container_run(version)

    # test
    print(green('testing ....'))
    prod_test(version)

    # stop
    print(green('stop all container....'))
    prod_container_stop(version)

    # push
    if push:
        print(green('push image to aliyun ....'))
        prod_push_image(version)


def replace_micro(version, micro):
    if (not version) or (not micro):
        abort('need version and network_bridge')

    local('docker stop' + micro + "_" + version)
    local('docker rm' + micro + "_" + version)

    with hide('running'):
        for cmd in yamlconfig['prod']['build']:
            with lcd(yamlconfig['project_path']):
                local(cmd)
