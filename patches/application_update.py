import sys
import json
from glob import glob
from utils import Deal_with_linux

class ApplicationUpdate:
    def __init__( self, jump_host, patch_num, sunny_path, application_hosts, application_path, tomcat_name, ansible_inventory, wars ):
        self.jump_host = jump_host
        self.patch_num = patch_num
        self.sunny_path = sunny_path
        self.sunny_patch = sunny_path + patch_num
        # application hosts as writen in ansible invenrory
        self.application_hosts = application_hosts
        self.application_path = application_path
        self.tomcat_name = tomcat_name
        self.ansible_inventory = ansible_inventory
        self.ansible_cmd_template = 'ansible -i ' + ansible_inventory + ' '
        # war files mappings. example [ 'pts-integration-' + patch_num + '.war', 'integration' ].
        self.wars = wars
        self.linux = Deal_with_linux()
			
    def get_ansible_result( self, paramiko_result ):
        ''' Convert paramiko result(string) to json '''
        
        a = paramiko_result
        #ansible_result = json.loads(a[a.find("{"):a.find("}")+1])
        # upper works incorrectly with multiple nested {}. Not shure if we need to propper terminate on last }?
        ansible_result = json.loads(a[a.find("{"):])
        return ansible_result
    
    def deal_with_tomcat( self, application_host, tomcat_name, tomcat_state ):
        ''' tomcat_name is systemd service name '''
    
        print "Attempting to make tomcat " + tomcat_state + "..."
        a = self.linux.linux_exec( self.jump_host, self.ansible_cmd_template + self.application_host + ' -m service -a "name=' + tomcat_name + ' state=' + tomcat_state + '" --become')
        ansible_result = get_ansible_result(a)
        if ansible_result['state'] == tomcat_state:
            print "OK: Tomcat " + tomcat_state
        elif ansible_result['state'] <> tomcat_state:
            print "FAIL: tomcat not " + tomcat_state + "!"
            sys.exit()
        else:
            print "FAIL: Error determining tomcat state!"
            sys.exit()
    
    # copy war files to asnible jump_host. check if already exists?
    def application_update( self ):
        print "Copy patch files from SUNNY to jumphost: " + self.jump_host
        for war in self.wars:
            if glob(self.sunny_patch + '\\' + war[0]) == []:
                print "ERROR: Unable to locate war file for " + war[0] + "!"
                sys.exit()
            war_path = glob( self.sunny_patch + '\\' + war[0])[0]
            self.linux.linux_put( self.jump_host, war_path, '/tmp/' + war[1] )

        #run ansibble command on every host sequentially (loop to be here)
        for application_host in self.application_hosts:
            print "Checking application files on " + application_host +":"
            app_to_update = False
            for war in self.wars:
                # check if wars on app_host  = wars from sunny
                a = self.linux.linux_exec( self.jump_host, self.ansible_cmd_template + application_host + ' -m copy -a "src=/tmp/' + war[1] +'.war dest=' + self.application_path + war[1] + '.war" --check' )
                ansible_result = self.get_ansible_result(a)
                #if changed = true set restart app flag to true
                if ansible_result['changed'] == True:
                    print "\t"+ war[1] + " needs to be updated."
                    app_to_update = True
            if app_to_update == False:
                print "\tNo application changed were made. Exiting."
                sys.exit()
            elif app_to_update == True:
                self.deal_with_tomcat( application_host, 'tomcat', 'stopped' )
                #TODO: only for updated wars...
                for war in self.wars:
                    # Remove deployed folders.
                    a = self.linux.linux_exec( jump_host, self.ansible_cmd_template + application_host + ' -m file -a "path=' + application_path + war[1] + ' state=absent" --become' )
                    # perform actual war copy. become?
                    print "Attempt to copy "+ war[1] + " to " + application_host + "..."
                    a = self.linux.linux_exec( self.jump_host, self.ansible_cmd_template + application_host + ' -m copy -a "src=/tmp/' + war[1] +'.war dest=' + application_path + war[1] + '.war" --become --become-user=tomcat' )
                    if 'SUCCESS' in a:
                        print "\tDone."
                    else:
                        print "\tERROR"
                        sys.exit
                # neet to variablize tomcat service name
                self.deal_with_tomcat( application_host, 'tomcat', 'started' )
            else:
                print "Something else"