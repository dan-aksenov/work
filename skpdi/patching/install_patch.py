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
import requests

''' Внутренние функции. ''' 

def usage():
    '''Функция "Инструкция по пременению" '''
    
    print 'Usage: -n for patch number(i.e. 2.10.1), -t for skpdi or predprod'

def md5_check( checked_file ):
    ''' Проверка md5 для war файлов '''
    
    md5sum = hashlib.md5(open(checked_file,'rb').read()).hexdigest()
    return md5sum

def linux_exec( linux_host, shell_command ):
    ''' Удаленное выполение команд на Linux '''
       
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
    ''' Копирование файлов на удаленный Linux '''
           
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
       # В дальнейшем удобнее манипулировать строковыми значениями, а не картежами. Поэтому результат прообразоваывается в массив строк.
        for row in rows:
            query_results.append(row[0])
    # Количество обработанных строк. Для просчета delete.
    rowcnt = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return query_results, rowcnt
    
def purge_panels():
    ''' Очистка панелей. Необходима перед при обновлении ПО, иногда даже при отстутствии патчей БД '''
  
    print "Purging panels on " + db_name + "@" + db_host + ": "
        
    # Завершить сессии приложения в БД если есть. Условие pid <> pg_backend_pid() для того чтобы не отрубал себя
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

    # Очистка временной директории. В Win, если "сидеть" в этой директории - будет ошибка.
    try:
        recreate_dir( stage_dir )
    except:
        print "ERROR: Unable to recreate patch staging directory."
        sys.exit()
    
    '''
    Блок установки патчей БД.
    '''
    # Блок нужно переработать. Слишком много вложений.
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
        # для отсечения суффиксов имен директорий с патчами (db_0190_20171113_v2.19) объявляетс отдельная переменная для патч max(patches_targ), иначе не удастся сравнить с тем что записано в БД. Возможно вместо sum надо использовать re.findall('db_.*_\d{8}',a), чтобы гарантированно получать номер патча.
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
                # Просмотре лога на предмет фразы "finsih install patch ods objects
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
            #Дополнетельная проверка. Выборка устанавливаемого патча из таблицы с патчами.
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
    TODO: План переработки. 1. Копироание файла на хост mon, c предварительной проверкой md5. 
    2. Копирование с mon на сервера приложений стандартным способом с проверкой md5. Возможно с помощью ansible(тк для него есть ключи и права root)
    Таким образом - копирование от нас с ЦОД будет проводиться только один раз, а не каждый раз, как сейчас.
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