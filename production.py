from fabric.api import task, lcd, local, hide, abort
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
            dfile = join(yamlconfig['env']['project_path'], yamlconfig['prod']['build_path'],
                         a + yamlconfig['prod']['image']['extensions'])
            f = open(dfile, 'w')
            f.write(content)
            f.close()


@task
def build_test():
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
def push_image_test(version):
    for cmd in yamlconfig['prod']['image']['push']:
        if ('{version}' in cmd) and ('{repo}' in cmd):
            cmd = cmd.format(repo=yamlconfig['env']['repo'],
                             version=version)
            print(cmd)
        else:
            abort('need {repo} {version}')
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


@task
def start_postgresql_test(version):
    cmd = yamlconfig['prod']['postgresql']['cmd']
    if ('{network_bridge}' in cmd) and ('{version}' in cmd):
        cmd = cmd.format(version=version, network_bridge=yamlconfig['env']['network_bridge'])
    else:
        abort('need {version} {network_bridge}')
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['prod']['postgresql']) and yamlconfig['prod']['postgresql']['init']:
        with hide('running'):
            if '{version}' in yamlconfig['prod']['postgresql']['init']:
                local((yamlconfig['prod']['postgresql']['init']).format(version=version))


@task
def start_redis_test(version):
    cmd = yamlconfig['prod']['redis']['cmd']
    if ('{network_bridge}' in cmd) and ('{version}' in cmd):
        cmd = cmd.format(version=version, network_bridge=yamlconfig['env']['network_bridge'])
    else:
        abort('need {version} {network_bridge}')
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['prod']['redis']) and yamlconfig['prod']['redis']['init']:
        local(yamlconfig['prod']['postgresql']['init'])


@task
def start_etcd_test(version):
    cmd = yamlconfig['prod']['etcd']['cmd']
    if ('{network_bridge}' in cmd) and ('{version}' in cmd):
        cmd = cmd.format(version=version, network_bridge=yamlconfig['env']['network_bridge'])
    else:
        abort('need {version} {network_bridge}')
    with hide('running'):
        local(cmd)

    if ('init' in yamlconfig['prod']['etcd']) and yamlconfig['prod']['etcd']['init']:
        local((yamlconfig['prod']['etcd']['init']).format(version=version))


@task
def start_base_test(version):
    start_postgresql_test(version)
    start_etcd_test(version)
    start_redis_test(version)


@task
def test_test(version):
    with lcd(yamlconfig['env']['project_path']):
        for cmd in yamlconfig['prod']['test']['cmd']:
            if ('{project_path}' in cmd) and ('{build_path}' in cmd) and ('{version}' not in cmd):
                cmd = cmd.format(project_path=yamlconfig['env']['project_path'],
                                 build_path=yamlconfig['prod']['build_path'])
                local(cmd)
            if ('{project_path}' in cmd) and ('{build_path}' in cmd) and ('{version}' in cmd) and (
                        '{network_bridge}' in cmd):
                cmd = cmd.format(project_path=yamlconfig['env']['project_path'],
                                 build_path=yamlconfig['prod']['build_path'], version=version,
                                 network_bridge=yamlconfig['env']['network_bridge'])
                local(cmd)


@task
def all_one():
    version = time.strftime(yamlconfig['env']['version'], time.localtime(time.time()))
    # start_etcd_test
    # print(version)
    # 测试用
    # TODO 清空环境的问题
    version = '03051307'
    start_base_test(version)
    container_run_test(version)
    test_test(version=version)
