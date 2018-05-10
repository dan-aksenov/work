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

sunny_path= '/sunny/builds/odsxp/'
# application hosts as writen in ansible invenrory
application_hosts = [ 'gudhskpdi-app-01', 'gudhskpdi-app-02' ]
application_path = '/u01/apache-tomcat-8.5.8/webapps/'
tomcat_name = 'tomcat'
ansible_inventory = '~/ansible-hosts/skpdi-prod'
wars = [
    [ 'skpdi-' + patch_num + '.war', 'skpdi' ],['ext-' + patch_num + '.war', 'ext']
    ]

a = ApplicationUpdate( jump_host, patch_num, sunny_path, application_hosts, application_path, tomcat_name, ansible_inventory, wars )

a.application_update()