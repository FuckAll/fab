from fabric.api import env
import site_config

from develop import *
import production
from settings import *



# from settings import *
# from docker_local import *
# from settings import *

# ssh config
env.use_ssh_config = True
env.user = 'root'
env.port = 22

# roledefs
env.roledefs = site_config.ROLEDEFS