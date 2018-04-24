import utils
import sys
import json
from glob import glob

# variables. to be moved to upper scripts
linux = utils.Deal_with_linux()
jump_host = "oemcc.fors.ru"
patch_num = '0.28.8.1'
sunny_patch = 'Y:\\pts\\' + patch_num
# application hosts as writen in ansible invenrory
application_hosts = ['pts-demo']
app_path = '/u01/apache-tomcat-8.5.27/webapps/'
tomcat_name = 'tomcat'
ansible_inventory = '~/ansible-hosts/pts-test'
ansible_cmd_template = 'ansible -i ' + ansible_inventory + ' '

def get_ansible_result( paramiko_result ):
    ''' Convert paramiko result(string) to json '''
    
    a = paramiko_result
    #ansible_result = json.loads(a[a.find("{"):a.find("}")+1])
    # upper works incorrectly with multiple nested {}. Not shure if we need to propper terminate on last }?
    ansible_result = json.loads(a[a.find("{"):])
    return ansible_result

def deal_with_tomcat( application_host, tomcat_name, tomcat_state ):
    ''' tomcat_name is systemd service name '''

    print "Attempting to make tomcat " + tomcat_state + "..."
    a = linux.linux_exec( jump_host, ansible_cmd_template + application_host + ' -m service -a "name=' + tomcat_name + ' state=' + tomcat_state + '" --become')
    ansible_result = get_ansible_result(a)
    if ansible_result['state'] == tomcat_state:
        print "OK: Tomcat " + tomcat_state
    elif ansible_result['state'] <> tomcat_state:
        print "FAIL: tomcat not " + tomcat_state + "!"
        sys.exit()
    else:
        print "FAIL: Error determining tomcat state!"
        sys.exit()

# war files mappings.
wars = [
    [ 'pts-integration-' + patch_num + '.war', 'integration' ],
    [ 'pts-public-' + patch_num + '.war', 'mobile' ],
    [ 'pts-restricted-' + patch_num + '.war', 'pts' ],
    [ 'pts-portal-' + patch_num + '.war', 'portal' ],
    [ 'pts-jointstorage-' + patch_num + '.war', 'jointstorage'  ]
    ]
                                                       
# check database version and apply database patch

# copy war files to asnible jump_host. check if already exists?
def main():
    '''print "Copy patch files from SUNNY to jumphost: " + jump_host
    for war in wars:
        if glob(sunny_patch + '\\' + war[0]) == []:
            print "ERROR: Unable to locate war file for " + war[0] + "!"
            sys.exit()
        war_path = glob( sunny_patch + '\\' + war[0])[0]
        linux.linux_put( jump_host, war_path, '/tmp/' + war[1] )
    '''
    #run ansibble command on every host sequentially (loop to be here)
    for application_host in application_hosts:
        print "Checking application files on " + application_host +":"
        app_to_update = False
        for war in wars:
            # check if wars on app_host  = wars on sunny
            a = linux.linux_exec( jump_host, ansible_cmd_template + application_host + ' -m copy -a "src=/tmp/webapps/' + war[1] +'.war dest=' + app_path + war[1] + '.war" --check' )
            ansible_result = get_ansible_result(a)
            #if changed = true set restart app flag to true
            if ansible_result['changed'] == True:
                print "\t"+ war[1] + " needs to be updated."
                app_to_update = True
        if app_to_update == False:
            print "\tNo application changed were made. Exiting."
            sys.exit()
        elif app_to_update == True:
            deal_with_tomcat( application_host, 'tomcat', 'stopped' )
            #TODO: only for updated wars...
            for war in wars:
                # Remove deployed folders.
                a = linux.linux_exec( jump_host, ansible_cmd_template + application_host + ' -m file -a "path=' + app_path + war[1] + ' state=absent" --become' )
                # perform actual war copy. become?
                print "Attempt to copy "+ war[1] + " to " + application_host + "..."
                a = linux.linux_exec( jump_host, ansible_cmd_template + application_host + ' -m copy -a "src=/tmp/webapps/' + war[1] +'.war dest=' + app_path + war[1] + '.war" --become --become-user=tomcat' )
                if 'SUCCESS' in a:
                    print "\tDone."
                else:
                    print "\tERROR"
                    sys.exit
            # neet to variablize tomcat service name
            deal_with_tomcat( application_host, 'tomcat', 'started' )
        else:
            print "Something else"
    
    # run serial task to update apps one by one from ansible host.
    # will restart of servers be serial too&
    # ansible run in python
if __name__ == "__main__":
    main()