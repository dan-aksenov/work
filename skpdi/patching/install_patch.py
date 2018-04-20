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

''' Internal functions ''' 

def usage():
    ''' Usage '''
    
    print 'Usage: -n for patch number(i.e. 2.10.1), -t for skpdi or predprod'
    
def purge_panels():
    ''' Purge application panels. Sometimes necessary even when no database patches applied '''
  
    print "Purging panels on " + db_name + "@" + db_host + ": "
        
    # Kill existing session. pid <> pg_backend_pid() so it won't kill self
    sess_killed = postgres_exec ( db_host, db_name,  "select pg_terminate_backend(pid) from pg_stat_activity where usename = 'ods' and pid <> pg_backend_pid()" )[1]
    print "\tKilled " + str(sess_killed) + " sessions of user ods in " + db_name + " database."
    rows_deleted = postgres_exec ( db_host, db_name,  'DELETE FROM core.fdc_sys_class_impl_lnk;' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_impl_lnk."
    rows_deleted = postgres_exec ( db_host, db_name,  'DELETE FROM core.fdc_sys_class_impl' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_impl."
    rows_deleted = postgres_exec ( db_host, db_name,  'DELETE FROM core.fdc_sys_class_panel_lnk;' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_panel_lnk."
    rows_deleted = postgres_exec ( db_host, db_name,  'DELETE FROM core.fdc_sys_class_panel;' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_panel.\n"
    
def check_webpage(patch_num, application_host, target):
    # redo it with /u01/apache-tomcat-8.5.23/webapps/record/META-INF/maven/ru.fors.ods/record/pom.xml version check?
	# cos it'll also work on pts
    ''' Seek version name in web page's code. '''

    page = requests.get('http://' + application_host + ":8080/" + target)
    if page.status_code <> 200:
       print Bcolors.WARING + "WARNING: Application webpage unnaccesseble: " + str(page.status_code) + "\n" + Bcolors.ENDC
    elif 'ver-' + patch_num in page.text:
        print Bcolors.OKGREEN + "SUCCESS: Application webpage matches " + patch_num + "\n" + Bcolors.ENDC
    elif 'ver-' + patch_num not in page.text:
        print Bcolors.WARING + "WARNING: Application webpage not matches " + patch_num + "\n" + Bcolors.ENDC
    else:
        print Bcolors.WARING + "WARING: Problem determining application version.\n" + Bcolors.ENDC

''' Internal functions. End '''
    
def main():
    
    '''
    Preparation
    '''
    
    linux = Deal_with_linux()
    
    # Check if patch exists on Sunny
    if os.path.isdir( sunny_patch ) != True:
        print Bcolors.FAIL + "ERROR: No such patch on Sunny!" + Bcolors.ENDC
        print "\tNo such directory " + sunny_patch
        sys.exit()

    # Clear temporary directory. May fall if somebody is "sitting" in it.
    try:
        recreate_dir( stage_dir )
    except:
        print Bcolors.FAIL + "ERROR: Unable to recreate patch staging directory." + Bcolors.ENDC
        sys.exit()
    
    '''
    Database patching
    '''
    # Get list of already applied patches
    # Function returns list tuples + row count, right now need only tuples, so [0]
    patches_curr = postgres_exec ( db_host, db_name,  'select name from parameter.fdc_patches_log order by id desc;' )[0]
    
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
            # Add additional check from database fdc_patches_log?
            #cur.execute("select name from parameter.fdc_patches_log where name = '" + i + "'")
            #is_db_patch_applied = postgres_exec ( db_host, db_name,  "select name from parameter.fdc_patches_log where name = '" + i + "'" )[0]
            #if is_db_patch_applied != []:
            #    pass    
            #else:    
            #    print "ERROR: Unable to confirm patch installation!"
            #    exit()
            
            # Purge panels.
            purge_panels()
   
        else:
            print "\tDatabase patch level: " + max(patches_curr)
            print "\t Latest patch on Sunny: " + last_patch_targ_strip
            print Bcolors.FAIL + "ERROR: Something wrong with database patching!\n" + Bcolors.ENDC
            sys.exit()
        
    '''
    Application update
    TODO: 1. copy war to gudhskpdi-mon, with md5 check. 
    2. copy from gudhskpdi-mon to app server with md5 check. Use ansible user (cos already has keys and root priveleges)
    '''
          
    print "Checking java application version:"
    # glob returns an array, need its first([0]) element to user in md5_check.
    # Search ods*war file in Sunny's patch directory. TODO what if there are more then one? Like on PTS.
    if glob( sunny_patch + '\\ods*.war' ) == []:
        print Bcolors.FAIL + "ERROR: Unable to locate war file on Sunny!" + Bcolors.ENDC
        sys.exit()
    
    war_path = glob( sunny_patch + '\\ods*.war' )[0]
    
    
    # Get application md5 from Sunny.
    source_md5 = md5_check( war_path )
    
    # Get application md5 from target server.
    # One by one comare of targets with source.
    # Get hosts_to_update list as result.
    
    hosts_to_update = []
    for i in application_host:
        target_md5 = linux.linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name )
        if source_md5 != target_md5.split(" ")[0]: 
            print "\tJava application on " + i + " will be updated."
            hosts_to_update.append(i)
    
    # Finish if hosts_to_update empty.
    if hosts_to_update == []:
        print Bcolors.OKBLUE + "\tAll application hosts already up to date." + Bcolors.ENDC
        sys.exit()  
 
    print "\n"
    
    for i in hosts_to_update:
        # Delete and recreate temporary directory for war file.
        linux.linux_exec( i, 'rm -rf /tmp/webapps && mkdir /tmp/webapps' )
        
        # Copy war to target server.
        print "Copying " + war_path + " to " + i + ":/tmp/webapps/" + war_name + "\n"
        linux.linux_put( i, war_path, '/tmp/webapps/' + war_name )
        linux.linux_exec( i, 'sudo chown tomcat.tomcat /tmp/webapps/' + war_name )
        
        # Stop tomcat server.
        print "Stopping application server " + i + "..."
        linux.linux_exec( i, 'sudo systemctl stop tomcat' )
        
    #for i in hosts_to_update:
        print "Applying application patch on " + i + "..."
        # Delete old application. Both warfile and directory.
        linux.linux_exec( i, 'sudo rm ' + app_path + '/' + war_name )
        linux.linux_exec( i, 'sudo rm -rf ' + app_path + '/' + war_fldr )
        
        # Copy war to webapps folder.
        linux.linux_exec( i, 'sudo cp /tmp/webapps/' + war_name + ' ' + app_path + '/' + war_name )
        
        print "Starting application server " + i + "..."
        linux.linux_exec( i, 'sudo systemctl start tomcat' )
        
        # Check if server really started.
        tcat_sctl = linux.linux_exec( i, 'sudo systemctl status tomcat' )
        tcat_status = tcat_sctl.find( 'Active: active (running) since' )
        if tcat_status != -1:
            print Bcolors.OKGREEN +"\tDone!\n" + Bcolors.ENDC
        else:
            print Bcolors.FAIL + "\tFailed!\n" + Bcolors.ENDC
        print "Waiting 60 seconds for application to (re)deploy..."
        sleep(60)
        check_webpage(patch_num, i, target)
    
    # Doublecheck md5.
    for i in hosts_to_update:
        target_md5 = linux.linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name )
        if source_md5 == target_md5.split(" ")[0]: 
            print Bcolors.OKGREEN + "DONE: Application version on " + i + " now matches " + patch_num + "." + Bcolors.ENDC
        else:
            print Bcolors.FAIL + "ERROR: Application version on " + i + " still not matches " + patch_num + "!" + Bcolors.ENDC

if __name__ == "__main__":
    
    # Get patch number and target environment from parameters n and t
    try:    
        opts, args = getopt( sys.argv[1:], 'n:t:h:' )
    except:
        usage()
        sys.exit()
    # Assign variables n - patch_num, t - target.
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
	    
    ''' Variables '''
    
	# If no parameter supplied prompt for them
    try:
        patch_num
    except:
        patch_num = raw_input('Enter patch number: ')
    try:
        target 
    except:
        target = raw_input('skpdi, predprod of manual: ')

    # Check for valid target name.    
    if target not in [ 'skpdi', 'predprod', 'manual']:
        usage()
        sys.exit()

    # Assign variables depending on target
    # Full variable explanation in 'manual' section
    if target == 'predprod':
        application_host = [ 'gudhskpdi-test-app' ]
        war_name = target + '.war'
        war_fldr = target
        db_patch_file = 'db_patch_generic.bat'
        db_name = 'ods_predprod'
        db_host = 'gudhskpdi-db-test'
    
    elif target == 'skpdi':
        application_host = [ 'gudhskpdi-app-01', 'gudhskpdi-app-02' ]
        war_name = target + '.war'
        war_fldr = target
        db_patch_file = 'db_patch_generic.bat'
        db_name = 'ods_prod'
        db_host = 'gudhskpdi-db-01'

    elif target == 'manual':
        # Input application hosts to array.
        application_host = list()
        num = raw_input("How many application servers? ")
        for i in range(int(num)):
            host_name = raw_input("Application server " + str(i) + ": ")
            application_host.append( host_name )

        # Directory with deployed application (predprod/skpdi)
        war_fldr = raw_input('Enter applicaton name (warfile name): ')    
        # warfile name (predprod.war/skpdi.war)
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
    stage_dir = 'd:\\tmp\\skpdi_patch'
    # Patch address on SUNNY
    sunny_path = '\\\sunny\\builds\\odsxp\\'
    # Exact directory path
    sunny_patch = sunny_path + patch_num
    # Tomcat webapps location on target server(s)
    tomcat_name = 'apache-tomcat-8.5.8'
    app_path = '/u01/' + tomcat_name + '/webapps'

    # Send subprocess for database patching to null. Nothing interesting there anyway.
    dnull = open("NUL", "w")

    ''' Variables. End.'''

    main()