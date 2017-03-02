from fabric.api import env, task, output
import site_config
from develop import *
from production import *
from docker_local import *
from settings import BASE_PREPARE_DIR, LOG_DIR, BASE_PROD_DIR

# ssh config
env.use_ssh_config = True
env.user = 'root'
env.port = 22

# roledefs
env.roledefs = site_config.ROLEDEFS


# nginx dev
@task
def host_type():
    run("uname -s")


@task
def all_mkdir():
    """[SA] 创建所有需要的目录"""
    for d in [BASE_PROD_DIR, BASE_PREPARE_DIR, LOG_DIR]:
        run('mkdir -p %s' % d)

# @task(alias='local')
# def local_run():
#     local("uname -s")
#
#
# def test():
#     with settings(warn_only=True):
#         result = local('uanme -sdf', capture=True)
#         if result.failed and not confirm("Tests Faild .Continue anyway?"):
#             abort("Aborting at user request.")
#
#
# def git_pull():
#     with lcd("/Users/KongFu/17mei/src/github.com/wothing/17mei-butler"):
#         local("git pull")
#
# @hosts('192.168.0.1','192.168.0.2')
# def ssh_dev():
#     with settings(warn_only=True):
#         d = "/"
#         if run("test -d %s" %d).failed:
#             run("uname -s ")
