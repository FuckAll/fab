from fabric.api import env
import site_config

from develop import *
from production import *
from settings import *
from docker_local import *


# ssh config
env.use_ssh_config = True
env.user = 'root'
env.port = 22

# roledefs
env.roledefs = site_config.ROLEDEFS