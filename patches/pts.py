from application_update import ApplicationUpdate
import utils

#Variables
jump_host = "oemcc.fors.ru"

# as parameter
patch_num = '0.28.8.1'

sunny_path= 'Y:\\pts\\'
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