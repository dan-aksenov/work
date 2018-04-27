from application_update import ApplicationUpdate
import utils

#Variables
jump_host = "oemcc.fors.ru"

# as parameter
patch_num = '3.3.3.2'

sunny_path= '/sunny/builds/odsxp/'
# application hosts as writen in ansible invenrory
application_hosts = [ 'gudhskpdi-app-01', 'gudhskpdi-app-02' ]
application_path = '/u01/apache-tomcat-8.5.8/webapps/'
tomcat_name = 'tomcat'
ansible_inventory = '~/ansible-hosts/skpdi-prod'
wars = [
    [ 'ods3-web-' + patch_num + '.war', 'skpdi' ],
    ]

a = ApplicationUpdate( jump_host, patch_num, sunny_path, application_hosts, application_path, tomcat_name, ansible_inventory, wars )

a.application_update()