from subprocess import call
from sys import argv, exit
# for db connection
from psycopg2 import connect
from os import listdir, rename
# for ssh connection.
import paramiko
# for war file search
from glob import glob
# for file md5s
import hashlib
import getopt

''' Переменные. Начало. '''

# Получение номера патча и контура установки(прод/предпрод) из параметров.
# Функция "Инструкция по пременению.
def usage():
    print 'Usage: -n for patch number(i.e. 2.10.1), -t for skpdi or demo'

# Прием параметров n и t, с дополнительной проверкой, что введены именно они.
try:    
    opts, args = getopt.getopt( argv[1:], 'n:t:' )
except:
    usage()
    exit()

# Назначение переменныч n - patch_num, t - target.
for opt, arg in opts:
    if opt in ( '-n' ):
        patch_num = arg
    elif opt in ( '-t' ):
        target = arg
    else:
        usage()
        exit()

# Если параметров не передано - запрашиваетя их воод их ввод.
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
'''
if target == 'skpdi':
    application_host = 'gudhskpdi-app-01' # Add app-02
    war_name = 'skpdi'
    db_patch_file = 'db_patch_skpdi.bat'
    db_name = 'ods_prod'
    db_host = 'gudhskpdi-db-01'
  
else:
    usage()
    exit()
'''

# Директория для временного хранения файлов установки
stage_dir = 'd:\\tmp\\skpdi_patch'
# Адрес хранилища SUNNY.
patch_store = '\\\sunny\\builds\\odsxp\\'
# Путь к директории с конкретным патчем.
patch_dir = patch_store + patch_num

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

''' Переменные. Конец.'''

''' Внутренние функции. Начало. ''' 

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

    sftp.put(localpath, remotepath)
    sftp.close()
    transport.close()

''' Внутренние функции. Конец. '''
    
'''
Блок подготовки.
'''

# Очистка временной директории. TODO: Redo it in python only w/o call.
call( [ 'rmdir', stage_dir, '/s', '/q' ], shell=True )
call( [ 'md', stage_dir ], shell=True )

'''
Блок установки патчей БД.
'''

#Подключение к БД и получение номеров уже устаноленных патей.
conn_string = 'dbname= ' + db_name + ' user=''ods'' password=''ods'' host=' + db_host
try:
    #redo it with variables
    conn = connect( conn_string )
except:
    print 'ERROR: unable to connect to the database!'
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
patches_targ = [ name for name in listdir( patch_dir + '\\patches' ) ]

# Сравненеие уже установленных патчей с патчами из директории.
# Если версия на БД младше чем лежит в директории с патчами, устанавливаются недостающие патчи.
print "Checking database patch level:\n"
if max(patches_targ) == max(patches_curr):
    print "\tNo database patches required.\n"
elif max(patches_targ) > max(patches_curr):
    print "\tDatabase needs patching.\n"
    patches_miss = []
    for i in (set(patches_targ) - set(patches_curr)):
        if i > max(patches_curr):
            patches_miss.append(i)

    print "Following database patches will be applied: " + ', '.join(patches_miss)
    for i in patches_miss:
        # Копирование только недостающих патчей с Sunny.
        call( [ 'xcopy', '/e', patch_dir + '\\patches' + i, stage_dir + '\\patches\\' + i  ], shell=True )
        # Копирование установщика патчей в директории с патчами.
        call( [ 'copy', '/y', db_patch_file , stage_dir + '\\patches\\' + i ], shell=True )

    # Остановка tomcat.
    for i in application_host:
        linux_exec( i, 'sudo systemctl stop tomcat' )
    # Установка патчей БД
    # Для выполенния по-порядку применен sort.
    for i in sorted(patches_miss):
        call( [ stage_dir + '\\patches\\' + i + '\\' + db_patch_file ], shell=True, cwd = stage_dir + '\\patches\\' + i)
    # Добавить: чтение и анализ лога установки.
else:
    print 'ERROR: Something wrong with database patching.'
    
'''
Блок обновления приложения.
'''

print "Checking java application version:\n"
# glob возвращает массив, поэтому для подстановки в md5_check изпользуется первый его элемент ([0]).
# Поиск файла ods*war в директории с патчем на sunny. Нужно добавить обработку если их вдруг будет больше одного.
war_path = glob( patch_dir + '\\ods*.war')[0]
# Получение md5 архива с приложением на Sunny.
source_md5 = md5_check( war_path )
# Получение md5 архива с приложением на целевом сервере приложения. Пока только для первого хоста в массиве.
target_md5 = linux_exec( application_host[0], 'sudo md5sum ' + app_path + '/' + war_name )

# Сравнение хешей приложения. target_md5.split(" ")[0] нужен для того, чтобы "причесать" linux вывод md5sum
if source_md5 == target_md5.split(" ")[0]: 
    print "\tNo application update required.\n"
    exit()
else:
    print "\tJava application will be updated.\n"

# Добавить: Учесть последовательное выполнение для 2 и более хостов приложений.
for i in application_host:
    linux_exec( i, 'rm -rf /tmp/webapps && mkdir /tmp/webapps' )
    print "Copying " + war_path + " to " + i + ":/tmp/webapps/"
    linux_put( i, war_path, '/tmp/webapps/' + war_name )
    linux_exec( i, 'sudo chown tomcat.tomcat /tmp/webapps/' + war_name )

# Остановить сервера приложений.
print "Stopping application servers..."
for i in application_host:
    linux_exec( i, 'sudo systemctl stop tomcat' )
    # Удалить старое приложение.
    linux_exec( i, 'sudo rm ' + app_path + '/' + war_name )
    linux_exec( i, 'sudo rm -rf ' + app_path + '/' + war_fldr )
    # Копировать war в целевую директорию на сервере приложений.
    linux_exec( i, 'sudo cp /tmp/webapps/' + war_name + ' ' + app_path + '/' + war_name )


# Еще раз проверить md5. Пока только для первого хоста в массиве.
target_md5 = linux_exec( application_host[0], 'sudo md5sum ' + app_path + '/' + war_name )
if source_md5 == target_md5.split(" ")[0]:
   print "Application version matches " + patch_num + "\n" 
else:
   print "ERROR: Application version not matches " + patch_num 	+ "\n" 

# Запустить сервера приложений.
for i in application_host:
    linux_exec( i, 'sudo systemctl start tomcat' )
    # Проверить работу сервера приложений после запуска.
    print linux_exec( i, 'sudo systemctl status tomcat' )