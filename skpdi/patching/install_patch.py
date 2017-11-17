# -*- coding: utf-8 -*-
# Для чтения русских комментов.

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

''' Переменные. '''

# Получение номера патча и контура установки(прод/предпрод) из параметров.
# Функция "Инструкция по пременению".
def usage():
    print 'Usage: -n for patch number(i.e. 2.10.1), -t for skpdi or predprod'

# Прием параметров n и t, с дополнительной проверкой, что введены именно они.
try:    
    opts, args = getopt( sys.argv[1:], 'n:t:h:' )
except:
    usage()
    sys.exit()

# Назначение переменныч n - patch_num, t - target.
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
    target = raw_input('skpdi or predprod? ')

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
    db_patch_file = 'db_patch_predprod.bat'
    
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
    db_patch_file = 'db_patch_skpdi.bat'
    
    # Имя БД.
    db_name = 'ods_prod'
    
    # Сервер БД.
    db_host = 'gudhskpdi-db-01'
    
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

''' Внутренние функции. ''' 

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
    ''' Пересоздание директории(удалить/создать) Windows '''
    
    if os.path.exists( dir_name ):
        shutil.rmtree( dir_name )
    else:
        os.makedirs( dir_name )

def postgres_exec( sql_query ):
    ''' Выполенение произвольного sql в базе
    Для получения списка патчей и очистки панелей '''
    
    conn_string = 'dbname= ' + db_name + ' user=''ods'' password=''ods'' host=' + db_host
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
    cur.close()
    conn.close()
    return query_results, rowcnt
    
def purge_panels():
    ''' Очистка панелей. Необходима перед при обновлении ПО, даже при отстутствии патчей БД '''
  
    print "Purging panels: "
    
    # Завершить сессии приложения в БД если есть. Решить вопрос с юзером БД. Сейчас отрубает сам себя.
    #sess_killed = postgres_exec ( "select pg_terminate_backend(pid) from pg_stat_activity where usename = 'ods'" )[1]
    #print "\tKilled " + str(sess_killed) + " sessions of user ods in " + db_name + " database."
    
    rows_deleted = postgres_exec ( 'DELETE FROM core.fdc_sys_class_impl_lnk;' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_impl_lnk."
    rows_deleted = postgres_exec ( 'DELETE FROM core.fdc_sys_class_impl' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_impl."
    rows_deleted = postgres_exec ( 'DELETE FROM core.fdc_sys_class_panel_lnk;' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_panel_lnk."
    rows_deleted = postgres_exec ( 'DELETE FROM core.fdc_sys_class_panel;' )[1]
    print "\tDeleted " + str(rows_deleted) + " rows from fdc_sys_class_panel.\n"
    
''' Внутренние функции. Конец. '''
    
def main():
    '''
    Блок подготовки.
    '''
    
    # Проверка наличия указанного патча на Sunny
    if os.path.isdir( sunny_patch ) != True:
        print "ERROR: No such patch on Sunny!"
        print "\tNo such directory " + sunny_patch
        sys.exit()

    # Очистка временной директории. В Win, если "сидеть" в этой директории - будет ошибка
    try:
        recreate_dir( stage_dir )
    except:
        print "ERROR: Unable to recreate patch staging directory."
        sys.exit()
    
    '''
    Блок установки патчей БД.
    '''
    # Блок нужно переработать. слишком много вложений.
    # Получеине списка уже устаноленных патей.
    # [0] потому что возвращает массив: кортежи + rowcount - нужны кортежи
    patches_curr = postgres_exec ( 'select name from parameter.fdc_patches_log order by id desc;' )[0]
    
    # Получение списка патчей БД из директории с патчами.
    # Добавить еще одну проверку чтение номера патча из файла define_version.sql на случай, если директорию назовут по другому.
    if os.path.isdir( sunny_patch + '\\patches' ) != True:
        print "NOTICE: No database patch found in build. Assume database patches not required."
    else:
        patches_targ = [ name for name in os.listdir( sunny_patch + '\\patches' ) ]
        
        # Сравненеие уже установленных патчей с патчами из директории.
        # Если версия на БД младше чем лежит в директории с патчами, устанавливаются недостающие патчи.
        print "\nChecking database patch level:"
        # для отсечения суффиксов имен директорий с патчами (db_0190_20171113_v2.19) объявляетс отдельная переменная для патч max(patches_targ), иначе не удастся сравнить с тем что записано в БД.
        last_patch_targ = max(patches_targ)
        last_patch_targ_strip = re.sub('_v.*$','', last_patch_targ)
        if last_patch_targ_strip == max(patches_curr):
            print "\tDatabase patch level: " + max(patches_curr) 
            print "\tLatest patch on Sunny: " + last_patch_targ_strip
            print "\tNo database patch required.\n"
        elif last_patch_targ_strip > max(patches_curr):
            print "\tDatabase patch level: " + max(patches_curr)
            print "\t Latest patch on Sunny: " + last_patch_targ_strip
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
            # Запуск tomcat в случае, если не удалось обновить базу.
            for i in application_host:
                print "Starting application server " + i + "...\n"
                linux_exec( i, 'sudo systemctl start tomcat' )
            sys.exit()
        
    '''
    Блок обновления приложения.
    '''
          
    print "Checking java application version:"
    # glob возвращает массив, поэтому для подстановки в md5_check изпользуется первый его элемент ([0]).
    # Поиск файла ods*war в директории с патчем на sunny. Нужно добавить обработку если их вдруг будет больше одного.
    if glob( sunny_patch + '\\ods*.war') == []:
        print "ERROR: Unable to locate war file!"
        sys.exit()
    
    war_path = glob( sunny_patch + '\\ods*.war')[0]
    
    
    # Получение md5 архива с приложением на Sunny.
    source_md5 = md5_check( war_path )
    
    # Получение md5 архива с приложением на целевом сервере приложения.
    # Последовательное сравнение с md5 на серверах приложений.
    # По результатам формируется список hosts_to_update для установки обновления.
    for i in application_host:
        target_md5 = linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name )
        hosts_to_update = []
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
        
        # Очистка панелей. Тут же останавливается сервера приложений.
        # Сделать очистку только один раз. В целом не критично.
        purge_panels()
        
        # Удалить старое приложение.
        print "Applying application patch on " + i + "..."
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
    
    # Еще раз проверить md5. Пока только для первого хоста в массиве. Может перенести в предъидущий цикл?
    for i in hosts_to_update:
        target_md5 = linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name )
        if source_md5 == target_md5.split(" ")[0]: 
            print "DONE: Application version on " + i + " now matches " + patch_num + ".\n"
        else:
            print "ERROR: Application version on " + i + " still not matches " + patch_num + "!\n"

if __name__ == "__main__":
    main()