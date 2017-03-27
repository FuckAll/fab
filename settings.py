# coding=utf-8
import json
from os.path import join
from os import environ
from fabric.api import abort, lcd, local, hide
import yaml
from fabric.contrib.files import exists

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
else:
    if 'build_path' not in yamlconfig['dev']:
        abort('prod need build_path')
    else:
        with hide('running'):
            with lcd(yamlconfig['project_path']):
                path = join(yamlconfig['project_path'], yamlconfig['dev']['build_path'])
                local('if [[ ! -d %s ]]; then mkdir ./%s; fi' % (path, yamlconfig['dev']['build_path']))

if 'prod' not in yamlconfig:
    abort('need prod')
else:
    if 'build_path' not in yamlconfig['prod']:
        abort('prod need build_path')
    else:
        with hide('running'):
            with lcd(yamlconfig['project_path']):
                path = join(yamlconfig['project_path'], yamlconfig['prod']['build_path'])
                local('if [[ ! -d %s ]]; then mkdir ./%s; fi' % (path, yamlconfig['prod']['build_path']))
