from application_update import ApplicationUpdate
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

sunny_path= '/sunny/builds/pts/'
# application hosts as writen in ansible invenrory
application_hosts = ['pts-demo']
application_path = '/u01/apache-tomcat-8.5.27/webapps/'
tomcat_name = 'tomcat'
ansible_inventory = '~/ansible-hosts/pts-test'
wars = [
    [ 'pts-integration-' + patch_num + '.war', 'integration' ],
    [ 'pts-public-' + patch_num + '.war', 'mobile' ],
    [ 'pts-restricted-' + patch_num + '.war', 'pts' ],
    [ 'pts-portal-' + patch_num + '.war', 'portal' ],
    [ 'pts-jointstorage-' + patch_num + '.war', 'jointstorage' ]
    ]

a = ApplicationUpdate( jump_host, patch_num, sunny_path, application_hosts, application_path, tomcat_name, ansible_inventory, wars )

a.application_update()