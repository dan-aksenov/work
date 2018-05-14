from application_update import ApplicationUpdate
from patch_database import PatchDatabase
import utils

from getopt import getopt
import sys, os

# Get patch number and target environment from parameters n and t
try:    
    opts, args = getopt( sys.argv[1:], 'n:' )
except:
    print "-n for patch number"
    sys.exit()

for opt, arg in opts:
    if opt in ( '-n' ):
        patch_num = arg
    else:
        print "-n for patch number"
        sys.exit()

#Variables
jump_host = "oemcc.fors.ru"
# application hosts as writen in ansible invenrory
application_hosts = ['gudhskpdi-app-02', 'gudhskpdi-app-01']
# // so windows can also read in correctly
sunny_path= '//sunny/builds/odsxp/'
application_path = '/u01/apache-tomcat-8.5.8/webapps/'
tomcat_name = 'tomcat'
ansible_inventory = '~/ansible-hosts/skpdi-prod'
wars = [
    [ 'skpdi-' + patch_num + '.war', 'skpdi' ],['ext-' + patch_num + '.war', 'ext']
    ]

db_host = 'gudhskpdi-db-01'
db_name = 'ods_prod'
db_user = 'ods'
patch_table = 'parameter.fdc_patches_log'
stage_dir = 'd:/tmp/skpdi_patch'

c = PatchDatabase(patch_num, sunny_path, application_hosts, ansible_inventory, db_host, db_name, stage_dir, db_user, patch_table)
c.patchdb()

a = ApplicationUpdate( jump_host, patch_num, sunny_path, application_hosts, application_path, tomcat_name, ansible_inventory, wars )
a.application_update()