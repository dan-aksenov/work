# -*- coding: utf-8 -*-
# for args and exit
import sys
# for db connection
from psycopg2 import connect
# for war file search
from glob import glob
from getopt import getopt
# for ssh connection and ftp transfer.
import paramiko
# for file md5s
import hashlib

# for correct patch number sorting 0.9.2 mast be before 0.20.1
from natsort import natsorted, ns

import subprocess
import shutil
import os

''' VARS '''

# Get patch number and target server
def usage():
    print 'Usage: -n for patch number(i.e. 2.10.1), -t for master or branch'

# Get n and t parameters
try:    
    opts, args = getopt( sys.argv[1:], 'n:t:h:' )
except:
    usage()
    sys.exit()

# Assign n - patch_num, t - target
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

# If params not supplied prompt for them
# raw_input used, so no need for additional quotes
try:
    patch_num
except:
    patch_num = raw_input('Enter patch number: ')

try:
    target        
except:
    target = raw_input('master or branch?')

# Correct target server or quit
if target not in [ 'master', 'branch' ]:
    usage()
    sys.exit()

# Assign variables, depending on target
    
if target == 'master':
    # Tomcat application server
    application_host = [ 'pts-tst-as1.fors.ru' ]
    
    # Имя файла приложения (predprod.war/skpdi.war).
    # war_name = target + '.war'
    # Директория с распакованным приложением (predprod/skpdi).
    # war_fldr = target
    # Батник для установки патчей БД.
    # db_patch_file = 'db_patch_predprod.bat'
    
    # Database name
    db_name = 'pts'
    
    # Database server
    db_host = '172.19.1.127'
    
elif target == 'branch':
    # Сервер приложения tomcat.
    application_host = [ 'pts-tst-as2.fors.ru' ]
    
    # Имя файла приложения (predprod.war/skpdi.war).
    # war_name = target + '.war'
    # Директория с распакованным приложением (predprod/skpdi).
    # war_fldr = target
    # Батник для установки патчей БД.
    db_patch_file = 'db_patch_skpdi.bat'
    
    # Имя БД.
    db_name = 'pts_branch'
    
    # Сервер БД.
    db_host = '172.19.1.127'
    
else:
    usage()
    sys.exit()

# Temporary storage
stage_dir = 'd:\\tmp\\pts'

# Sunny builds address
sunny_path = '\\\sunny\\builds\\pts\\'
# Current patch directory
sunny_patch = sunny_path + patch_num

'''
war files mappings. Format: [ 'name on sunny', 'desired application name']
'''
war_integration = [ 'pts-integration-*.war', 'integration.war' ]
war_portal = [ 'pts-public-*.war', 'portal.war' ]
war_pts = [ 'pts-restricted-*.war', 'pts.war' ]
war_portal2 = [ 'pts-portal*.war', 'portal2.war' ]
war_jointstorate = [ 'pts-jointstorage*.war', 'jointstorage.war' ]


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
tomcat_name = 'apache-tomcat-8.5.4'
app_path = '/opt/' + tomcat_name + '/webapps'

# Для перенаправления вывода subprocess при установке патча БД. Там все равно нет ничего интересного.
dnull = open("NUL", "w")

''' VARS. End '''

''' Internal functions ''' 

def md5_check( checked_file ):
    ''' Проверка md5 для war файлов '''
    
    md5sum = hashlib.md5(open(checked_file,'rb').read()).hexdigest()
    return md5sum

def linux_exec( linux_host, shell_command ):
    ''' Удаленное выполение команд на Linux '''
       
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect( hostname = linux_host, username = ssh_user, port = ssh_port, pkey = linux_key )
    
    stdin, stdout, stderr = client.exec_command( shell_command )
    data = stdout.read() + stderr.read()
    client.close()
    return data

def linux_put( linux_host, source_path, dest_path ):
    ''' Копирование файлов на удаленный Linux '''
           
    transport = paramiko.Transport(( linux_host, ssh_port ))
    transport.connect( username = ssh_user, pkey = linux_key )
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

def postgres_exec ( sql_query ):
    ''' Execute query in database '''
    # pgpass should be used insead of password    
    conn_string = 'dbname= ' + db_name + ' user=''postgres'' host=' + db_host
    try:
        conn = connect( conn_string )
    except:
        print '\nERROR: unable to connect to the database!'
        sys.exit()
    cur = conn.cursor()
    cur.execute( sql_query )
    query_results = []
    # Эта проверка нужна, так как при удалении нет курсора, который можно будет вернуть.
    if cur.description != None:
        rows = cur.fetchall()
       # В дальнейшем удобнее манипулировать строковыми значениями, а не картежами. Поэтому результат прообразоваывается в массим строк.
        for row in rows:
            query_results.append(row[0])
    # Количество обработанных строк. Для просчета delete.
    rowcnt = cur.rowcount
    conn.commit()
    # Закрытие курсора и коннекта не обязательно, просто для порядка.
    cur.close()
    conn.close()
    return query_results, rowcnt

def war_compare( war_name ):
    print "Checking java application version:"
    # glob returns array, using first [0] element to use in in md5_check.
    # Search war file on in target directory on sunny. TODO: what if more then one candidate?
    if glob(sunny_patch + '\\' + war_name[0]) == []:
        print "ERROR: Unable to locate war file for " + war_portal[1] + "!"
        sys.exit()

    war_path = glob( sunny_patch + '\\' + war_name[0])[0]

    # Get war's md5 from sunny.
    source_md5 = md5_check( war_path )

    # Get war's md5 from target applicaton server.
    # Compare Sunny's war whit target server's war.
    # По результатам формируется список hosts_to_update для установки обновления.
    for i in application_host:
        target_md5 = linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name[1] + '.war' )
        hosts_to_update = []
        if source_md5 != target_md5.split(" ")[0]: 
            print "\t Applicatoin " + war_name[1] + " on " + i + " will be updated."
            hosts_to_update.append(i)
        return hosts_to_update

def war_update( war_name, hosts_to_update ):
    # to be here
    return result
        
''' Internal functions. End '''
    
'''
Preparations
'''

# Проверка наличия указанного патча на Sunny
if os.path.isdir( sunny_patch ) != True:
    print "ERROR: No such patch on Sunny!"
    print "\tNo such directory " + sunny_patch
    sys.exit()

# Очистка временной директории.
recreate_dir( stage_dir )

'''
DB patches install
'''

# Получеине списка уже устаноленных патей.
# [0] потомучто массив значений - на первой позиции.
patches_curr = postgres_exec ( 'select name from parameter.fdc_patches_log order by id desc;' )[0]

# Получение списка патчей БД из директории с патчами.
# Переделать под птс
patches_targ = [ name for name in os.listdir( sunny_pach ) ]

# Сравненеие уже установленных патчей с патчами из директории.
# Если версия на БД младше чем лежит в директории с патчами, устанавливаются недостающие патчи.
print "\nChecking database patch level:"
if max(patches_targ) == max(patches_curr):
    print "\tNo database patch required.\n"
elif max(patches_targ) > max(patches_curr):
    print "\tDatabase needs patching.\n"
    patches_miss = []
    for i in (set(patches_targ) - set(patches_curr)):
        if i > max(patches_curr):
            patches_miss.append(i)

    print "Following database patches will be applied: " + ', '.join(patches_miss) + "\n"
    for i in patches_miss:
        # Копирование только недостающих патчей с Sunny.
        subprocess.call( [ 'xcopy', '/e', '/i', '/q', sunny_patch + '\\patches\\' + i, stage_dir + '\\patches\\' + i  ], stdout=dnull, shell=True )
        # Копирование установщика патчей в директории с патчами.
        subprocess.call( [ 'copy', '/y', db_patch_file , stage_dir + '\\patches\\' + i ], stdout=dnull, shell=True )

    # Остановка tomcat.
    for i in application_host:
        print "Stopping application server " + i + "...\n"
        linux_exec( i, 'sudo systemctl stop tomcat' )
    # Установка патчей БД
    # Для выполенния по-порядку применен sort.
    for i in sorted(patches_miss):    
        print "Applying database patch " + i + "..."
        # Вывод отправлен в null - тк там все равно ничего по делу. Результат будет анализирован через чтение лога.
        subprocess.call( [ stage_dir + '\\patches\\' + i + '\\' + db_patch_file ], stdout=dnull, stderr = dnull, shell = False, cwd = stage_dir + '\\patches\\' + i )
        # Просмотре лога на предмет фразы "finsih install patch ods objects"
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
            print "\tError installing database patch.\n"
            sys.exit()
        logfile.close()
        # Дополнетельная проверка. Выборка устанавливаемого патча из таблицы с патчами.
        is_db_patch_applied = postgres_exec("select name from parameter.fdc_patches_log where name = '" + i + "'")
        if is_db_patch_applied != []:
            pass    
        else:    
            print "ERROR: Unable to confirm patch installation!"
            exit()
    
else:
    print "ERROR: Something wrong with database patching!\n"
    
'''
Application patches install.
'''

# print "Checking java application version:"
# Moved to functions 


# Просто для форматирования.    
print "\n"


# to be replaced with function ...
for i in hosts_to_update:
    #/need separate function for war update?
    # Удалить и пересоздать директорию для временного хранения war файла.
    linux_exec( i, 'rm -rf /tmp/webapps && mkdir /tmp/webapps' )
    
    # Скопировать war файл на сервер приложений.
    print "Copying " + war_path + " to " + i + ":/tmp/webapps/" + war_name + "\n"
    linux_put( i, war_path, '/tmp/webapps/' + war_name )
    linux_exec( i, 'sudo chown tomcat.tomcat /tmp/webapps/' + war_name )
    
    # Остановить сервер приложений.
    print "Stopping application server " + i + "..."
    linux_exec( i, 'sudo systemctl stop tomcat' )
    
    # Удалить старое приложение.
    print "Applying application patch on " + i + "..."
    linux_exec( i, 'sudo rm ' + app_path + '/' + war_name )
    linux_exec( i, 'sudo rm -rf ' + app_path + '/' + war_fldr )
    
    # Копировать war в целевую директорию на сервере приложений.
    linux_exec( i, 'sudo cp /tmp/webapps/' + war_name + ' ' + app_path + '/' + war_name )
    print "Starting application server " + i + "..."
    linux_exec( i, 'sudo systemctl start tomcat' )
    
    # Проверить работу сервера приложений после запуска.
    tcat_sctl = linux_exec( i, 'sudo systemctl status tomcat' )
    tcat_status = tcat_sctl.find( 'Active: active (running) since' )
    if tcat_status != -1:
        print "\tDone!\n"
    else:
        print "\tFailed!\n"

# Final md5 check. To be replaced with function.
for i in hosts_to_update:
    target_md5 = linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name )
    if source_md5 == target_md5.split(" ")[0]: 
        print "DONE: Application version on " + i + " now matches " + patch_num + ".\n"
    else:
        print "ERROR: Application version on " + i + " still not matches " + patch_num + "!\n"