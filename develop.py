
from fabric.api import task, hosts, run, cd, settings
from site_config import ROLEDEFS
from settings import *

@task
@hosts(ROLEDEFS['dev'])
def dev_nginx():
    git_pull()


# git_pull nginx
def git_pull():
    code_dir = os.path.join(BASE_PREPARE_DIR + '17mei-ops')
    with settings(warn_only=True):
        if run("test -d %s" % code_dir).failed:
            run("git clone %s" % MEI_OPS)
    with cd(code_dir):
        run('git pull')
        run("git log -1 |grep commit|awk '{print $2}' > .revision")


@task
@hosts(ROLEDEFS['nginx'])
def prod_nginx():
    git_pull()