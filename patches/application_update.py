import sys
import json
from glob import glob
from utils import Deal_with_linux, md5_check

class ApplicationUpdate:
    def __init__( self, jump_host, patch_num, sunny_path, application_hosts, application_path, tomcat_name, ansible_inventory, wars ):
        # intermediate host with ansible installation.
        self.jump_host = jump_host
        self.patch_num = patch_num
        self.sunny_path = sunny_path
        self.sunny_patch = sunny_path + patch_num + '/'
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
        a = self.linux.linux_exec( self.jump_host, self.ansible_cmd_template + application_host + ' -m service -a "name=' + tomcat_name + ' state=' + tomcat_state + '" --become')
        ansible_result = self.get_ansible_result(a)
        if ansible_result['state'] == tomcat_state:
            print "OK: Tomcat " + tomcat_state
        elif ansible_result['state'] <> tomcat_state:
            print "FAIL: tomcat not " + tomcat_state + "!"
            sys.exit()
        else:
            print "FAIL: Error determining tomcat state!"
            sys.exit()

    def application_update( self ):
        
        # TODO add check if patch path on sunny
        for application_host in self.application_hosts:
            print "Checking application files on " + application_host +":"
            app_to_update = False
            for war in self.wars:
                # check if wars on app_host  = wars from sunny
                paramiko_result = self.linux.linux_exec( self.jump_host, self.ansible_cmd_template + application_host + ' -m copy -a "src=' + self.sunny_patch + war[0] + ' dest=' + self.application_path + war[1] + '.war" --check --become --become-user=tomcat' )
                ansible_result = self.get_ansible_result(paramiko_result)
                # if changed = true set restart app flag to true
                # deal if not success!!!
                if 'SUCCESS' in paramiko_result:
                    if ansible_result['changed'] == True:
                        print "\t"+ war[1] + " application needs to be updated."
                        app_to_update = True
                elif 'FAILED' in paramiko_result:
                    print paramiko_result
                    sys.exit()
                else:
                    print paramiko_result
                    sys.exit()
            if app_to_update == False:
                print "\tApplications version on "+ application_host +" already " + self.patch_num
                sys.exit()
            elif app_to_update == True:
                self.deal_with_tomcat( application_host, 'tomcat', 'stopped' )
                #TODO: only for updated wars...
                for war in self.wars:
                    # Remove deployed folders.
                    paramiko_result = self.linux.linux_exec( self.jump_host, self.ansible_cmd_template + application_host + ' -m file -a "path=' + self.application_path + war[1] + ' state=absent" --become' )
                    # perform actual war copy. become?
                    print "Attempt to copy "+ war[1] + " to " + application_host + "..."
                    paramiko_result = self.linux.linux_exec( self.jump_host, self.ansible_cmd_template + application_host + ' -m copy -a "src='  + self.sunny_patch + war[0] + ' dest=' + self.application_path + war[1] + '.war" --become --become-user=tomcat' )
                    # TODO supress if particular app not needs updating
                    if 'SUCCESS' in paramiko_result:
                        print "\tSuccesfully updated application " + war[1] + " on " + application_host
                    else:
                        print paramiko_result
                        sys.exit
                # neet to variablize tomcat service name
                self.deal_with_tomcat( application_host, 'tomcat', 'started' )
            else:
                print "Something else"