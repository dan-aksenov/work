from application_update import ApplicationUpdate
from patch_database import PatchDatabase
import utils

from getopt import getopt
import sys
import os

# Get patch number and target environment from parameters n and t
try:
    opts, args = getopt(sys.argv[1:], 'n:')
except StandardError:
    print "-n for patch number"
    sys.exit()

for opt, arg in opts:
    if opt in ('-n'):
        patch_num = arg
    else:
        print "-n for patch number"
        sys.exit()

# Variables
# host to run ansible commands from
jump_host = "oemcc.fors.ru"
ansible_inventory = '~/ansible-hosts/skpdi-prod'
# application hosts as writen in ansible invenrory
application_hosts = ['gudhskpdi-app-02', 'gudhskpdi-app-01']
# // so windows can also read it correctly, same as linux
sunny_path = '//sunny/builds/odsxp/'
# tomcat application location
application_path = '/u01/apache-tomcat-8.5.8/webapps/'
# sysinit or systemd service name to stop/start server
tomcat_name = 'tomcat'
# war files mappings
wars = [
    ['skpdi-' + patch_num + '.war', 'skpdi'],
    ['ext-' + patch_num + '.war', 'ext']
    ]

db_host = 'gudhskpdi-db-01'
db_name = 'ods_prod'
db_user = 'ods'
# databaes table to look for current db_version
patch_table = 'parameter.fdc_patches_log'
# temporary directory to hold database patches.
stage_dir = 'd:/tmp/skpdi_patch'

d = PatchDatabase(
    patch_num,
    sunny_path,
    application_hosts,
    ansible_inventory,
    db_host,
    db_name,
    stage_dir,
    db_user,
    patch_table
   )

d.patchdb()

a = ApplicationUpdate(
    jump_host,
    patch_num,
    sunny_path,
    application_hosts,
    application_path,
    tomcat_name,
    ansible_inventory,
    wars
   )

a.application_update()
