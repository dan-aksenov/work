# -*- coding: utf-8 -*-
# Ru comment read. to be removed

# for args and exit
import sys
# for db connection
from psycopg2 import connect
#from os import os.listdir, os.rename, rmdir, os.path, os.makedirs
# for war file search
from glob import glob
from getopt import getopt
# for ssh connection and ftp transfer.
import paramiko
# for file md5s
import hashlib

import subprocess
import shutil
import os
import re
import requests

''' Internal functions ''' 

def usage():
    ''' Usage '''
    
    print 'Usage: -n for patch number(i.e. 2.10.1), -t for skpdi or predprod'

def md5_check( checked_file ):
    ''' *.war file md5 check '''
    
    md5sum = hashlib.md5(open(checked_file,'rb').read()).hexdigest()
    return md5sum

def linux_exec( linux_host, shell_command ):
    ''' Linux remote execution '''
       
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect( hostname = linux_host, username = ssh_user, port = ssh_port, pkey = linux_key )
    except:
        print '\nERROR: unable to connect to Linux machine!'
        sys.exit()
    stdin, stdout, stderr = client.exec_command( shell_command )
    data = stdout.read() + stderr.read()
    client.close()
    return data

def linux_put( linux_host, source_path, dest_path ):
    ''' Copy to remote Linux '''
           
    transport = paramiko.Transport(( linux_host, ssh_port ))
    try:
        transport.connect( username = ssh_user, pkey = linux_key )
    except:
        print '\nERROR: unable to connect to Linux machine!'
        sys.exit()
    sftp = paramiko.SFTPClient.from_transport( transport )
    
    localpath = source_path
    remotepath = dest_path

    sftp.put( localpath, remotepath )
    sftp.close()
    transport.close()

def recreate_dir( dir_name ):
    ''' Recreate Windows directory '''
    
    if os.path.exists( dir_name ):
        shutil.rmtree( dir_name )
    else:
        os.makedirs( dir_name )

def postgres_exec( sql_query ):
    ''' SQL execution '''
    
    conn_string = 'dbname= ' + db_name + ' user=''ods'' password=''ods'' host=' + db_host
    try:
        conn = connect( conn_string )
    except:
        print '\nERROR: unable to connect to the database!'
        sys.exit()
    cur = conn.cursor()
    cur.execute( sql_query )
    query_results = []
    # This check needed, because delete doesn't return cursor
    if cur.description != None:
        rows = cur.fetchall()
       # Need list of stings instead of tuples for future manipulation.
        for row in rows:
            query_results.append(row[0])
    rowcnt = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return query_results, rowcnt
    
def purge_panels():
    ''' Purge application panels. Sometimes necessary even when no database patches applied '''
  
    print "Purging panels on " + db_name + "@" + db_host + ": "
        
    # Kill existing session. pid <> pg_backend_pid() so it won't kill self
    sess_killed = postgres_exec ( "select pg_terminate_backend(pid) from pg_stat_activity where usename = 'ods' and pid <> pg_backend_pid()" )[1]
    print "\tKilled " + str(sess_killed) + " sessions of user ods in " + db_name + " database."
    
    rows_deleted = postgres_exec ( 'DELETE FROM core.fdc_sys_class_impl_lnk;' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_impl_lnk."
    rows_deleted = postgres_exec ( 'DELETE FROM core.fdc_sys_class_impl' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_impl."
    rows_deleted = postgres_exec ( 'DELETE FROM core.fdc_sys_class_panel_lnk;' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_panel_lnk."
    rows_deleted = postgres_exec ( 'DELETE FROM core.fdc_sys_class_panel;' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_panel.\n"
    
def check_webpage():
    # todo redo it with /u01/apache-tomcat-8.5.23/webapps/record/META-INF/maven/ru.fors.ods/record/pom.xml version check?
    ''' Seek version name in web page's come. '''

    proxies = {
      'http': 'http://cache.fors.ru:3128',
      'https': 'http://cache.fors.ru:3128'
    }

    page = requests.get('http://skpdi.mosreg.ru/' + target, proxies=proxies)
    if page.status_code <> 200:
       print "WARNING: Application webpage unnaccesseble: " + page.status_code
    elif 'ver-' + patch_num in page.text:
        print "SUCCESS: Application webpages matches " + patch_num
    elif 'ver-' + patch_num not in page.text:
        print "WARNING: Application webpages not matches! " + patch_num
    else:
        print "WARING: Problem determining application version."

''' Internal functions. End '''
    
def main():
    '''
    Preparation
    '''
    
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
    '''
    # TODO: decrease number of "nests"
    # Get list of already applied patches
    # Function returns list tuples + row count, right now need only tuples, so [0]
    patches_curr = postgres_exec ( 'select name from parameter.fdc_patches_log order by id desc;' )[0]
    
    # Get list of patches from from Sunny
    # Add one more check for patch version based on define_version.sql.
    if os.path.isdir( sunny_patch + '\\patches' ) != True:
        print "NOTICE: No database patch found in build. Assume database patches not required."
    else:
        patches_targ = [ name for name in os.listdir( sunny_patch + '\\patches' ) ]
        
        # Compare installed patches with patches from Sunny.
        # If latest database patch version lower then on Sunny - install missing patches.
        print "\nChecking database patch level:"
        # To handle file name suffixes for directories like "db_0190_20171113_v2.19" additional variable declared to hold max(patches_targ)
        # Or else unable to compare with database. Maybe need to use re.findall('db_.*_\d{8}',a).
        last_patch_targ = max(patches_targ)
        last_patch_targ_strip = re.sub('_v.*$','', last_patch_targ)
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
                linux_exec( i, 'sudo systemctl stop tomcat' )
            # Apply database patches
            # Using sort to execute patches in right order.
            for i in sorted(patches_miss):    
                print "Applying database patch " + i + "..."
                # Output to null - nothing usefull there anyway. Result to be analyzed by reading log. 
                subprocess.call( [ stage_dir + '\\patches\\' + i + '\\' + db_patch_file, db_host, db_name  ], stdout=dnull, stderr = dnull, shell = False, cwd = stage_dir + '\\patches\\' + i )
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
            # Additional check from database fdc_patches_log...
            #cur.execute("select name from parameter.fdc_patches_log where name = '" + i + "'")
            #is_db_patch_applied = postgres_exec ( "select name from parameter.fdc_patches_log where name = '" + i + "'" )[0]
            #if is_db_patch_applied != []:
            #    pass    
            #else:    
            #    print "ERROR: Unable to confirm patch installation!"
            #    exit()
   
        else:
            print "\tDatabase patch level: " + max(patches_curr)
            print "\t Latest patch on Sunny: " + last_patch_targ_strip
            print "ERROR: Something wrong with database patching!\n"
            # Start tomcat if base was not patched.
            for i in application_host:
                print "Starting application server " + i + "...\n"
                linux_exec( i, 'sudo systemctl start tomcat' )
            sys.exit()
        
    '''
    Application update
    TODO: 1. copy war to gudhskpdi-mon, with md5 check. 
    2. copy from gudhskpdi-mon to app server with md5 check. Use ansible user (cos already has keys and root priveleges)
    '''
          
    print "Checking java application version:"
    # glob возвращает массив, поэтому для подстановки в md5_check изпользуется первый его элемент ([0]).
    # Поиск файла ods*war в директории с патчем на sunny. Нужно добавить обработку если их вдруг будет больше одного.
    if glob( sunny_patch + '\\ods*.war') == []:
        print "ERROR: Unable to locate war file on Sunny!"
        sys.exit()
    
    war_path = glob( sunny_patch + '\\ods*.war')[0]
    
    
    # Получение md5 архива с приложением на Sunny.
    source_md5 = md5_check( war_path )
    
    # Получение md5 архива с приложением на целевом сервере приложения.
    # Последовательное сравнение с md5 на серверах приложений.
    # По результатам формируется список hosts_to_update для установки обновления.
    
    hosts_to_update = []
    for i in application_host:
        target_md5 = linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name )
        if source_md5 != target_md5.split(" ")[0]: 
            print "\tJava application on " + i + " will be updated."
            hosts_to_update.append(i)
    
    # Завершить работу, если в hosts_to_update пусто.
    if hosts_to_update == []:
        print "\tAll application hosts already up to date."
        sys.exit()  
    
    # Просто для форматирования.    
    print "\n"
    
    for i in hosts_to_update:
        # need separate function for war update?
        # Удалить и пересоздать директорию для временного хранения war файла.
        linux_exec( i, 'rm -rf /tmp/webapps && mkdir /tmp/webapps' )
        
        # Скопировать war файл на сервер приложений.
        print "Copying " + war_path + " to " + i + ":/tmp/webapps/" + war_name + "\n"
        linux_put( i, war_path, '/tmp/webapps/' + war_name )
        linux_exec( i, 'sudo chown tomcat.tomcat /tmp/webapps/' + war_name )
        
        # Остановить сервер приложений.
        print "Stopping application server " + i + "..."
        linux_exec( i, 'sudo systemctl stop tomcat' )
        
    # Очистка панелей. Вынесена в отдельный блок тк нужна только один раз.
    purge_panels()
        
    for i in hosts_to_update:
        print "Applying application patch on " + i + "..."
        # Удалить старое приложение. war-файл и папку.
        linux_exec( i, 'sudo rm ' + app_path + '/' + war_name )
        linux_exec( i, 'sudo rm -rf ' + app_path + '/' + war_fldr )
        
        # Копировать war в целевую директорию на сервере приложений.
        linux_exec( i, 'sudo cp /tmp/webapps/' + war_name + ' ' + app_path + '/' + war_name )
        
        print "Starting application server " + i + "..."
        linux_exec( i, 'sudo systemctl start tomcat' )
        
        # Проверить состояние сервера приложений после запуска.
        tcat_sctl = linux_exec( i, 'sudo systemctl status tomcat' )
        tcat_status = tcat_sctl.find( 'Active: active (running) since' )
        if tcat_status != -1:
            print "\tDone!\n"
        else:
            print "\tFailed!\n"
    
    # Еще раз проверить md5
    for i in hosts_to_update:
        target_md5 = linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name )
        if source_md5 == target_md5.split(" ")[0]: 
            print "DONE: Application version on " + i + " now matches " + patch_num + ".\n"
        else:
            print "ERROR: Application version on " + i + " still not matches " + patch_num + "!\n"

if __name__ == "__main__":
    ''' Переменные. '''
    # Получение номера патча и контура установки(прод/предпрод) из параметров.
    # Прием параметров n и t, с дополнительной проверкой, что введены именно они.
    try:    
        opts, args = getopt( sys.argv[1:], 'n:t:h:' )
    except:
        usage()
        sys.exit()

    # Назначение переменных n - patch_num, t - target.
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

# Если параметры не переданы - запрашиваетя их ввод.
# raw_input используется, для того, чтоб вводить без кавычек.
    try:
        patch_num
    except:
        patch_num = raw_input('Enter patch number: ')

    try:
        target 
    except:
        target = raw_input('skpdi, predprod: ')

    # Проверка правильного указания контура установки skpdi или predprod.    
    if target not in [ 'skpdi', 'predprod']:
        usage()
        sys.exit()

    # В зависимости от контура назначаются остальные переменные.
    if target == 'predprod':
        # Сервер приложения tomcat.
        application_host = [ 'gudhskpdi-test-app' ]
    
        # Имя файла приложения (predprod.war/skpdi.war).
        war_name = target + '.war'
    
        # Директория с распакованным приложением (predprod/skpdi).
        war_fldr = target
    
        # Батник для установки патчей БД.
        db_patch_file = 'db_patch_generic.bat'
    
        # Имя БД.
        db_name = 'ods_predprod'
    
        # Сервер БД.
        db_host = 'gudhskpdi-db-test'
    
    elif target == 'skpdi':
        # Сервер приложения tomcat.
        application_host = [ 'gudhskpdi-app-01', 'gudhskpdi-app-02' ]
    
        # Имя файла приложения (predprod.war/skpdi.war).
        war_name = target + '.war'
    
        # Директория с распакованным приложением (predprod/skpdi).
        war_fldr = target
    
        # Батник для установки патчей БД.
        db_patch_file = 'db_patch_generic.bat'
    
        # Имя БД.
        db_name = 'ods_prod'
    
        # Сервер БД.
        db_host = 'gudhskpdi-db-01'

    #elif target == 'manual':
        # Сервер приложения tomcat.
        # application_host = raw_input('Enter application host: ')
    
        # Имя файла приложения (predprod.war/skpdi.war).
        # war_name = target + '.war'
    
        # Директория с распакованным приложением (predprod/skpdi).
        # war_fldr = target
    
        # Батник для установки патчей БД.
        #db_patch_file = 'db_patch_generic.bat'
    
        # Имя БД.
        #db_name = raw_input('Enter database name: ')
    
        # Сервер БД.
        #db_host = raw_input('Enter database server hostname: ')
    
    else:
        usage()
        sys.exit()

    # Директория для временного хранения файлов установки
    stage_dir = 'd:\\tmp\\skpdi_patch'

    # Адрес хранилища SUNNY.
    sunny_path = '\\\sunny\\builds\\odsxp\\'
    # Путь к директории с конкретным патчем.
    sunny_patch = sunny_path + patch_num

    ''' Linux stuff '''
    # Путь к расположения ключа SSH. Если такого нет - выход. Довавить возможность менять его?
    linux_key_path = 'C:\Users\daniil.aksenov\Documents\ssh\id_rsa.key'
    if os.path.isfile( linux_key_path ) != True:
       print "ERROR: Linux ssh key " + linux_key_path + " not found!"
       sys.exit()

    # Ключ SSH подготовленный для работы paramiko.
    linux_key = paramiko.RSAKey.from_private_key_file( linux_key_path )
    # Пользователь SSH.
    ssh_user = 'ansible'
    # Порт SSH.
    ssh_port = 22

    # Версия и расположение приложений Tomcat.
    tomcat_name = 'apache-tomcat-8.5.8'
    app_path = '/u01/' + tomcat_name + '/webapps'

    # Для перенаправления вывода subprocess при установке патча БД. Там все равно нет ничего интересного.
    dnull = open("NUL", "w")

    ''' Переменные. Конец.'''

    main()
    
    # Дополнительный поиск номера патча на веб странице
    check_webpage()