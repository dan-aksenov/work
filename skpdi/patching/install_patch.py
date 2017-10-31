from subprocess import call
from sys import argv, exit
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

import shutil
import os

''' Переменные. '''

# Получение номера патча и контура установки(прод/предпрод) из параметров.
# Функция "Инструкция по пременению".
def usage():
    print 'Usage: -n for patch number(i.e. 2.10.1), -t for skpdi or demo'

# Прием параметров n и t, с дополнительной проверкой, что введены именно они.
try:    
    opts, args = getopt( argv[1:], 'n:t:h:' )
except:
    usage()
    exit()

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
        exit()

# Если параметры не переданы - запрашиваетя их ввод.
# raw_input используется, для того, чтоб вводить без кавычек.
try:
    patch_num
except:
    patch_num = raw_input('Enter patch number: ')

try:
    target        
except:
    target = raw_input('skpdi or demo? ')

# Проверка правильного указания контура установки skpdi или demo.    
if target not in [ 'skpdi', 'demo']:
    usage()
    exit()

# В зависимости от контура назначаются остальные переменные.
    
if target == 'demo':
    # Сервер приложения tomcat.
    application_host = [ 'gudhskpdi-test-app' ]
    
    # Имя файла приложения (demo.war/skpdi.war).
    war_name = target + '.war'
    
    # Директория с распакованным приложением (demo/skpdi).
    war_fldr = target
    
    # Батник для установки патчей БД.
    db_patch_file = 'db_patch_demo.bat'
    
    # Имя БД.
    db_name = 'ods_demo'
    
    # Сервер БД.
    db_host = 'gudhskpdi-db-test'
    
elif target == 'skpdi':
    # Сервер приложения tomcat.
    application_host = [ 'gudhskpdi-app-01', 'gudhskpdi-app-02' ]
    
    # Имя файла приложения (demo.war/skpdi.war).
    war_name = target + '.war'
    
    # Директория с распакованным приложением (demo/skpdi).
    war_fldr = target
    
    # Батник для установки патчей БД.
    db_patch_file = 'db_patch_skpdi.bat'
    
    # Имя БД.
    db_name = 'ods_prod'
    
    # Сервер БД.
    db_host = 'gudhskpdi-db-01'
    
else:
    usage()
    exit()

# Директория для временного хранения файлов установки
stage_dir = 'd:\\tmp\\skpdi_patch'

# Адрес хранилища SUNNY.
sunny_path = '\\\sunny\\builds\\odsxp\\'
# Путь к директории с конкретным патчем.
sunny_patch = sunny_path + patch_num

''' Linux stuff '''
# Путь к расположения ключа SSH.
linux_key_path = 'C:\Users\daniil.aksenov\Documents\ssh\id_rsa.key'
# Ключ SSH подготовленный для работы paramiko.
linux_key = paramiko.RSAKey.from_private_key_file( linux_key_path )
# Пользователь SSH.
ssh_user = 'ansible'
# Порт SSH.
ssh_port = 22

# Версия и расположение приложений Tomcat.
tomcat_name = 'apache-tomcat-8.5.8'
app_path = '/u01/' + tomcat_name + '/webapps'

# Для перенаправления вывода subprocess при установке патча БД. Там все равно нет ничего интересного
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

''' Внутренние функции. Конец. '''
    
'''
Блок подготовки.
'''

# Очистка временной директории.

if os.path.exists( stage_dir ):
    shutil.rmtree( stage_dir )
else:
    os.makedirs( stage_dir )


'''
Блок установки патчей БД.
'''

#Подключение к БД и получение номеров уже устаноленных патей.
conn_string = 'dbname= ' + db_name + ' user=''ods'' password=''ods'' host=' + db_host
try:
    #redo it with variables
    conn = connect( conn_string )
except:
    print '\nERROR: unable to connect to the database!'
    # Exit if unable to connect.
    exit()
cur = conn.cursor()
cur.execute('''select name from parameter.fdc_patches_log order by id desc;''')
rows = cur.fetchall()
patches_curr = []
# Transform from tuples to strings to compare with patches_targ
for row in rows:
    patches_curr.append(row[0])

# Получение списка патчей БД из директории с патчами.
patches_targ = [ name for name in os.listdir( sunny_patch + '\\patches' ) ]

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
        call( [ 'xcopy', '/e', '/i', '/q', sunny_patch + '\\patches\\' + i, stage_dir + '\\patches\\' + i  ], stdout=dnull, shell=True )
        # Копирование установщика патчей в директории с патчами.
        call( [ 'copy', '/y', db_patch_file , stage_dir + '\\patches\\' + i ], stdout=dnull, shell=True )

    # Остановка tomcat.
    for i in application_host:
        print "Stopping application server " + i + "...\n"
        linux_exec( i, 'sudo systemctl stop tomcat' )
    # Установка патчей БД
    # Для выполенния по-порядку применен sort.
    for i in sorted(patches_miss):	
        print "Applying database patch " + i + "..."
        # Вывод отправлен в null - тк там все равно ничего по делу. Результат будет анализирован через чтение лога
        call( [ stage_dir + '\\patches\\' + i + '\\' + db_patch_file ], stdout=dnull, stderr = dnull, shell = False, cwd = stage_dir + '\\patches\\' + i)
        # Просмотре лога на предмет фразы "finsih install patch ods objects"
        try:
            logfile = open( stage_dir + '\\patches\\' + i + '\\install_db_log.log' )
        except:
            print "\tUnable to read logfile. Somethnig wrong with installation.\n"
            exit()
        loglines = logfile.read()
        success_marker = loglines.find('finsih install patch ods objects')
        if success_marker != -1:
            print "\tDone.\n"
        else:
            print "\tError installing database patch.\n"
            exit()
        logfile.close()
    # Очистка панелей
    print "Purging panels: "
    cur.execute('''DELETE FROM core.fdc_sys_class_impl_lnk;''')
    print "\tDeleted " + str(cur.rowcount) + " rows from fdc_sys_class_impl_lnk."
    cur.execute('''DELETE FROM core.fdc_sys_class_impl;''')
    print "\tDeleted " + str(cur.rowcount) + " rows from fdc_sys_class_impl."
    cur.execute('''DELETE FROM core.fdc_sys_class_panel_lnk;''')
    print "\tDeleted " + str(cur.rowcount) + " rows from fdc_sys_class_panel_lnk."
    cur.execute('''DELETE FROM core.fdc_sys_class_panel;''')
    print "\tDeleted " + str(cur.rowcount) + " rows from fdc_sys_class_panel.\n"
    # Обязательно нужно делать commit, иначе сессия останется в idle in transaction.
    conn.commit()
    # Закрытие курсора и коннекта не обязательно, просто для порядка.
    cur.close()
    conn.close()
else:
    print "ERROR: Something wrong with database patching!\n"
    
'''
Блок обновления приложения.
'''

print "Checking java application version:"
# glob возвращает массив, поэтому для подстановки в md5_check изпользуется первый его элемент ([0]).
# Поиск файла ods*war в директории с патчем на sunny. Нужно добавить обработку если их вдруг будет больше одного.
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
    print "\tAll application hosts alreasy up to date."
    exit()   

# Просто для форматирования.    
print "\n"

for i in hosts_to_update:
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

# Еще раз проверить md5. Пока только для первого хоста в массиве. Может перенести в предъидущий цикл?
for i in hosts_to_update:
    target_md5 = linux_exec( i, 'sudo md5sum ' + app_path + '/' + war_name )
    if source_md5 == target_md5.split(" ")[0]: 
        print "DONE: Application version on " + i + " now matches " + patch_num + ".\n"
    else:
        print "ERROR: Application version on " + i + " still not matches " + patch_num + "!\n"