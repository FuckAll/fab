# coding=utf-8
import json
from os.path import join
from os import environ
from fabric.api import lcd

# file need to create
BASE_PROD_DIR = '/17mei/prod/'
BASE_PREPARE_DIR = '/17mei/prepare/'
LOG_DIR = 'log'
# NGINX_CONF_DIR = 'conf/nginx/'
# NGINX_CONF_PREPARE_DIR = os.path.join(BASE_PREPARE_DIR, NGINX_CONF_DIR)
# NGINX_CONF_PROD_DIR = os.path.join(BASE_PROD_DIR, NGINX_CONF_DIR)

# github repo
MEI_OPS = "git@github.com:wothing/17mei-ops.git"
FABENB = {}


# docker image
containers = {
    'redis': 'daocloud.io/izgnod/redis:latest',
    'postgres': 'daocloud.io/izgnod/postgres:latest',
    'etcd': 'daocloud.io/izgnod/etcd:latest'
}


# env
with lcd('~'):
    f = open(join(environ.get('HOME'), ".fab"))
    s = f.read()
    FABENB = json.loads(s)
    f.close()

