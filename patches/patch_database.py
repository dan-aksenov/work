# for args and exit
import sys
import os
# for war file search
from glob import glob
from getopt import getopt
# for waiting
from time import sleep
# for coloured output
from termcolor import colored

import subprocess
import shutil
import os
import re
import requests

#Custom utilities
from utils import md5_check, recreate_dir, Deal_with_linux, postgres_exec, Bcolors
    
# NOTE: purge_panels to be moved to skpdi specific.
    
''' Internal functions. End '''

class PatchDatabase:
    #def __init__( self, patch_num, sunny_path, application_hosts, ansible_inventory, patches_table ):
    def __init__( self ):
	#def __init__( self, jump_host, patch_num, sunny_path, application_hosts, ansible_inventory, patches_table ):
        # intermediate host with ansible installation.
        #self.jump_host = jump_host
        self.patch_num = '3.4'
        #self.sunny_path = sunny_path
        self.stage_dir = 'd:\\tmp\\skpdi_patch'
        self.sunny_path = '\\\sunny\\builds\\odsxp\\'
        self.sunny_patch = self.sunny_path + self.patch_num + '/'
        # sunny_patch = sunny_path + patch_num
        # application hosts as writen in ansible invenrory
        self.application_hosts = 'gudhskpdi-test-app'
        #self.ansible_inventory = '~/ansible-hosts'
        #self.ansible_cmd_template = 'ansible -i ' + ansible_inventory + ' '
        # patches_table - variable to hold db_patches_log(specific in different projects)
        self.patch_table = ''
        self.linux = Deal_with_linux()
        # Send subprocess for database patching to null. Nothing interesting there anyway.
        self.dnull = open("NUL", "w")
    
    def patchdb( self ):
        '''
        Preparation
        '''
        # Check if patch exists on Sunny
        if os.path.isdir( self.sunny_patch ) != True:
            print Bcolors.FAIL + "ERROR: No such patch on Sunny!" + Bcolors.ENDC
            print "\tNo such directory " + self.sunny_patch
            sys.exit()

        # Clear temporary directory. May fall if somebody is "sitting" in it.
        try:
            recreate_dir( self.stage_dir )
        except:
            print Bcolors.FAIL + "ERROR: Unable to recreate patch staging directory." + Bcolors.ENDC
            sys.exit()
    
        '''
        Database patching
        '''
        # Get list of already applied patches
        # Function returns list tuples + row count, right now need only tuples, so [0]
        patches_curr = postgres_exec ( db_host, db_name,  'select name from '+ patches_table +' order by id desc;' )[0]
    
        # Get list of patches from from Sunny
        if os.path.isdir( sunny_patch + '\\patches' ) != True:
            print "NOTICE: No database patch found in build. Assume database patching not required."
        else:
            patches_targ = [ name for name in os.listdir( sunny_patch + '\\patches' ) ]
        
            # Compare installed patches with patches from Sunny.
            # If latest database patch version lower then on Sunny - install missing patches.
            print "\nChecking database patch level:"
            # To handle file name suffixes for directories like "db_0190_20171113_v2.19" additional variable declared to hold max(patches_targ)
            last_patch_targ = max( patches_targ )
            last_patch_targ_strip = re.findall('db_.*_\d{8}', last_patch_targ)[0] # findall returns list
            if last_patch_targ_strip == max(patches_curr):
                print "\tDatabase patch level: " + max(patches_curr) 
                print "\tLatest patch on Sunny: " + last_patch_targ_strip
                print "\tNo database patch required.\n"
            elif last_patch_targ_strip > max(patches_curr):
                print "\tDatabase patch level: " + max(patches_curr)
                print "\tLatest patch on Sunny: " + last_patch_targ_strip
                print "\tDatabase needs patching.\n"
                patches_miss = []
                for i in (set(patches_targ) - set(patches_curr)):
                    if i > max(patches_curr):
                        patches_miss.append(i)
    
                print "Following database patches will be applied: " + ', '.join(patches_miss) + "\n"
                for i in patches_miss:
                # Copy needed patches from Sunny.
                    subprocess.call( [ 'xcopy', '/e', '/i', '/q', sunny_patch + '\\patches\\' + i, stage_dir + '\\patches\\' + i  ], stdout=dnull, shell=True )
                # Place patch installer to patch subdirectories.
                    subprocess.call( [ 'copy', '/y', db_patch_file , stage_dir + '\\patches\\' + i ], stdout=dnull, shell=True )
    
            # Stop tomcat.
                for i in application_hosts:
                    print "Stopping application server " + i + "...\n"
                    linux.linux_exec( i, 'sudo systemctl stop tomcat' )
                # Apply database patches
                # Using sort to execute patches in right order.
                for i in sorted(patches_miss):    
                    print "Applying database patch " + i + "..."
                    # Output to null - nothing usefull there anyway. Result to be analyzed by reading log. 
                    subprocess.call( [ stage_dir + '\\patches\\' + i + '\\' + db_patch_file, db_host, db_name, db_port, db_user ], stdout=dnull, stderr = dnull, shell = False, cwd = stage_dir + '\\patches\\' + i )
                    # Search logfile for "finish install patch ods objects
                    try:
                        logfile = open( stage_dir + '\\patches\\' + i + '\\install_db_log.log' )
                    except:
                        print Bcolors.FAIL + "\tUnable to read logfile" + stage_dir + "\\patches\\" + i + "\\install_db_log.log. Somethnig wrong with installation.\n" + Bcolors.ENDC
                        sys.exit()
                    loglines = logfile.read()
                    success_marker = loglines.find('finsih install patch ods objects')
                    if success_marker != -1:
                        print Bcolors.OKGREEN + "\tDone.\n" + Bcolors.ENDC
                    else:
                        print Bcolors.FAIL + "\tError installing database patch. Examine logfile " + stage_dir + "\\patches\\" + i + "\\install_db_log.log for details\n" + Bcolors.ENDC
                        sys.exit()
                    logfile.close()
          
            else:
                print "\tDatabase patch level: " + max(patches_curr)
                print "\t Latest patch on Sunny: " + last_patch_targ_strip
                print Bcolors.FAIL + "ERROR: Something wrong with database patching!\n" + Bcolors.ENDC
                sys.exit()