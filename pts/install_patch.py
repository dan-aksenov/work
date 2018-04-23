# for args and exit
import sys
# for db connection
from psycopg2 import connect
#from os import os.listdir, os.rename, rmdir, os.path, os.makedirs
# for war file search
from glob import glob
from getopt import getopt
# moved to utils
#import paramiko
#import hashlib
# for waiting
from time import sleep
# for coloured output
from termcolor import colored

import subprocess
import shutil
import os
import re
import requests

from utils import md5_check, recreate_dir, Deal_with_linux, postgres_exec

''' Internal functions ''' 

def usage():
    ''' Usage '''
    
    print 'Usage: -n for patch number(i.e. 0.29.1), -t for master or predprod'

linux = Deal_with_linux()

def war_compare( target_host, war_name ):
    print "Checking java application version for " + war_name[1] + ":"
    # glob returns array, using first [0] element to use in in md5_check.
    # Search war file on in target directory on sunny.
    if glob(sunny_patch + '\\' + war_name[0]) == []:
        print "ERROR: Unable to locate war file for " + war_name[0] + "!"
        sys.exit()

    war_path = glob( sunny_patch + '\\' + war_name[0])[0]

    # Get war's md5 from sunny.
    source_md5 = md5_check( war_path )

    # Get war's md5 from target applicaton server.
    # Compare Sunny's war whit target server's war.

    # hosts_to_upate needs to be removed or set as global...
    target_md5 = linux.linux_exec( target_host, 'sudo md5sum ' + app_path + '/' + war_name[1])
    if source_md5 != target_md5.split(" ")[0]: 
        print "\t Applicatoin " + war_name[1] + " on " + target_host + " will be updated."
        #where to_update to be initialized?
        host_to_update = target_host
        app_to_update_src = war_name[0]
        app_to_update_dst = war_name[1]
    else:
        print "\t Applicatoin " + war_name[1] + " on " + target_host + " matches target."
        #host_to_update = ''
        #app_to_update=''
    return host_to_update, app_to_update_src, app_to_update_dst
                                                                
''' Internal functions. End '''
    
def main():
    '''
    Preparation
    '''
    
    #linux = Deal_with_linux()
    
    # Check if patch exists on Sunny
    if os.path.isdir( sunny_patch ) != True:
        print "ERROR: No such patch on Sunny!"
        print "\tNo such directory " + sunny_patch
        sys.exit()

    # Clear temporary directory. May fall if somebody is "sitting" in it.
    try:
        recreate_dir( stage_dir )
    except:
        print "ERROR: Unable to recreate patch staging directory."
        sys.exit()
    
    '''
    Database patching
    
    # Get list of already applied patches
    # Function returns list tuples + row count, right now need only tuples, so [0]
    patches_curr = postgres_exec ( db_host, db_name,  'select name from parameter.patches_log order by id desc;' )[0]
    
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
            for i in application_host:
                print "Stopping application server " + i + "...\n"
                linux.linux_exec( i, 'sudo systemctl stop tomcat' )
            # Apply database patches
            # Using sort to execute patches in right order.
            for i in sorted(patches_miss):    
                print "Applying database patch " + i + "..."
                # Output to null - nothing usefull there anyway. Result to be analyzed by reading log. 
                subprocess.call( [ stage_dir + '\\patches\\' + i + '\\' + db_patch_file, db_host, db_name ], stdout=dnull, stderr = dnull, shell = False, cwd = stage_dir + '\\patches\\' + i )
                # Search logfile for "finish install patch ods objects
                try:
                    logfile = open( stage_dir + '\\patches\\' + i + '\\install_db_log.log' )
                except:
                    print "\tUnable to read logfile. Somethnig wrong with installation.\n"
                    sys.exit()
                loglines = logfile.read()
                success_marker = loglines.find('finsih install patch ods objects')
                if success_marker != -1:
                    print "\tDone.\n"
                else:
                    print "\tError installing database patch. Examine logfile " + stage_dir + '\\patches\\' + i + '\\install_db_log.log' + "\n"
                    sys.exit()
                logfile.close()
   
        else:
            print "\tDatabase patch level: " + max(patches_curr)
            print "\t Latest patch on Sunny: " + last_patch_targ_strip
            print "ERROR: Something wrong with database patching!\n"
            sys.exit()
        

    Application update
    '''

    # list to hold hosts and wars for updating
    to_update = []
    for host in application_host:
        for war in wars:
            host_to_update, app_to_update_src, app_to_update_dst = war_compare( host, war )
            to_update.append( [host_to_update, app_to_update_src, app_to_update_dst] )
    
    # Finish if to_update empty.
    if to_update == []:
        print "\tAll application hosts already up to date."
        sys.exit()
 
    print "\n"
    
    # debug hosts to update
    print to_update


    for host_to_update, app_to_update_src, app_to_update_dst in to_update:
        # Delete and recreate temporary directory for war file.
#        linux.linux_exec( i, 'rm -rf /tmp/webapps && mkdir /tmp/webapps' )
        
        # Copy war to target server.
        print "Copying " + app_to_update_src + " to " + host_to_update + ":/tmp/webapps/" + app_to_update_dst + "\n"
#        linux.linux_put( i, war_path, '/tmp/webapps/' + war_name )
#        linux.linux_exec( i, 'sudo chown tomcat.tomcat /tmp/webapps/' + war_name )
        
        # Stop tomcat server.
        print "Stopping application server " + host_to_update + "..."
#        linux.linux_exec( i, 'sudo systemctl stop tomcat' )
        
    #for i in to_update:
        print "Applying application patch on " + host_to_update + "..."
        # Delete old application. Both warfile and directory.
#        linux.linux_exec( i, 'sudo rm ' + app_path + '/' + war_name )
#        linux.linux_exec( i, 'sudo rm -rf ' + app_path + '/' + war_fldr )
        
        # Copy war to webapps folder.
#        linux.linux_exec( i, 'sudo cp /tmp/webapps/' + war_name + ' ' + app_path + '/' + war_name )
        
        print "Starting application server " + host_to_update + "..."
#        linux.linux_exec( i, 'sudo systemctl start tomcat' )
        
        # Check if server really started.
        tcat_sctl = linux.linux_exec( host_to_update, 'sudo systemctl status tomcat' )
        tcat_status = tcat_sctl.find( 'Active: active (running) since' )
        if tcat_status != -1:
            print "\tDone!\n"
        else:
            print "\tFailed!\n"
        print "Waiting 60 seconds for application to (re)deploy..."
#        sleep(60)
#        check_webpage(patch_num, i, target)

    # Doublecheck md5. to be rewritten!
    #for i in to_update:
     #   target_md5 = linux.linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name )
      #  if source_md5 == target_md5.split(" ")[0]: 
       #     print colored("DONE: Application version on " + i + " now matches " + patch_num + ".", 'white', 'on_green')
        #else:
         #   print colored("ERROR: Application version on " + i + " still not matches " + patch_num + "!", 'white', 'on_red')

if __name__ == "__main__":
    ''' Variables '''
    # Get patch number and target environment from parameters n and t
    try:    
        opts, args = getopt( sys.argv[1:], 'n:t:h:' )
    except:
        usage()
        sys.exit()

    # Assibn variables n - patch_num, t - target.
    for opt, arg in opts:
        if opt in ( '-n' ):
            patch_num = arg
        elif opt in ( '-t' ):
            target = arg
        elif opt in ( '-h' ):
            usage()
        else:
            usage()
            sys.exit()

# If no parameter supplied prompt for them
    try:
        patch_num
    except:
        patch_num = raw_input('Enter patch number: ')

    try:
        target 
    except:
        target = raw_input('master or manual: ')

    # Check for valid target name.    
    if target not in [ 'master', 'branch', 'manual']:
        usage()
        sys.exit()

    # Assign variables depending on target
    # Full variable explanation in 'manual' section
    if target == 'master':
        application_host = [ 'pts-tst-as1' ]
        war_name = target + '.war'
        war_fldr = target
        db_patch_file = 'db_patch_test.bat'
        db_name = 'pts'
        db_host = '172.19.1.127'
    
    elif target == 'branch':
        application_host = [ 'pts-tst-as2' ]
        war_name = target + '.war'
        war_fldr = target
        db_patch_file = 'db_patch_test.bat'
        db_name = 'pts_branch'
        db_host = '172.19.1.127'
    
    elif target == 'manual':
        # Input application hosts to array.
        application_host = list()
        num = raw_input("How many application servers? ")
        for i in range(int(num)):
            host_name = raw_input("Application server " + str(i) + ": ")
            application_host.append( host_name )

        # Directory with deployed application (predprod/fishery)
        war_fldr = raw_input('Enter applicaton name (warfile name): ')    

        # warfile name (predprod.war/fishery.war)
        war_name = war_fldr + '.war'
               
        # batfile for database patching
        db_patch_file = 'db_patch_generic.bat'
       
        # database server
        db_host = raw_input('Enter database server hostname: ')
        
        # database name
        db_name = raw_input('Enter database name: ')
    
    else:
        usage()
        sys.exit()

    # Patchfile temporary directory
    stage_dir = 'd:\\tmp\\pts_patch'

    # Patch address on SUNNY
    sunny_path = '\\\sunny\\builds\\pts\\'
    # Exact directory path
    sunny_patch = sunny_path + patch_num

    # Tomcat webapps location on target server(s)
    tomcat_name = 'apache-tomcat-8.5.27'
    app_path = '/opt/' + tomcat_name + '/webapps'

    # Send subprocess for database patching to null. Nothing interesting there anyway.
    dnull = open("NUL", "w")
    
    '''
    war files mappings. Format: [ 'name on sunny', 'desired application name']
    '''
    wars = [
    [ 'pts-integration-' + patch_num + '.war', 'integration.war' ],
    [ 'pts-public-' + patch_num + '.war', 'mobile.war' ],
    [ 'pts-restricted-' + patch_num + '.war', 'pts.war' ],
    [ 'pts-portal-' + patch_num + '.war', 'portal.war' ],
    [ 'pts-jointstorage-' + patch_num + '.war', 'jointstorage.war'  ]
    ]
    
    ''' Variables. End.'''

    main()