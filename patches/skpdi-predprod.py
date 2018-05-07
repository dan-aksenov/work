from application_update import ApplicationUpdate
import utils

#Variables
jump_host = "oemcc.fors.ru"

# as parameter
patch_num = '3.3.3.5'

sunny_path= '/sunny/builds/odsxp/'
# application hosts as writen in ansible invenrory
application_hosts = ['gudhskpdi-test-app']
application_path = '/u01/apache-tomcat-8.5.8/webapps/'
tomcat_name = 'tomcat'
ansible_inventory = '~/ansible-hosts/skpdi-prod'
wars = [
    [ 'skpdi-' + patch_num + '.war', 'predprod' ],['ext-' + patch_num + '.war', 'ext-predprod']
    ]

a = ApplicationUpdate( jump_host, patch_num, sunny_path, application_hosts, application_path, tomcat_name, ansible_inventory, wars )

a.application_update()