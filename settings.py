# coding=utf-8
import json
from os.path import join
from os import environ
from fabric.api import task, abort
import yaml

yamlconfig = ''
f = open(join(environ.get('HOME'), ".fab.yaml"), 'r')
y = yaml.load(f)
yamlconfig = y

if 'project_name' not in yamlconfig:
    abort('need project_name')

if 'project_path' not in yamlconfig:
    abort('need project_path')

if 'sql_dir' not in yamlconfig:
    abort('need sql_dir')

if 'repo' not in yamlconfig:
    abort('need repo')

if 'version' not in yamlconfig:
    abort('need version')

if 'dockerfile_extensions' not in yamlconfig:
    abort('need dockerfile_extensions')

if 'network_bridge' not in yamlconfig:
    abort('need network_bridge')

if 'dev' not in yamlconfig:
    abort('need dev')

if 'prod' not in yamlconfig:
    abort('need prod')
