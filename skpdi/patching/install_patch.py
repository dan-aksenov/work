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

def usage():
    print 'Usage: -n for patch number, -t skpdi or demo'

''' Переменные. Начало. '''
''' Получение номера патча и контура установки(прод/предпрод) из параметров '''
opts, args = getopt.getopt( argv[1:], 'n:t:' )
for opt, arg in opts:
    if opt in ( '-n' ):
        patch_num = arg
    elif opt in ( '-t' ):
        target = arg
    else:
        usage()
        exit()

''' Если параметров не передано - запросить их ввод '''        
try:
    patch_num
except:
    patch_num = raw_input('Enter patch number: ')

try:
    target        
except:
    target = raw_input('skpdi or demo? ')
        
if target not in [ 'skpdi', 'demo']:
    usage()
    exit()
        
if target == 'demo':
    application_host = 'gudhskpdi-test-app'
    war_name = target + '.war'
    war_fldr = target
    db_patch_file = 'db_patch_demo.bat'
    db_name = 'ods_demo'
    db_host = 'gudhskpdi-db-test'

'''
if target == 'skpdi':
    application_host = 'gudhskpdi-app-01' # Add app-02
    war_name = 'skpdi'
    db_patch_file = 'db_patch_skpdi.bat'
    db_name = 'ods_prod'
    db_host = 'gudhskpdi-db-01'
'''    

# Stage dir to hold patch data.
stage_dir = 'd:\\tmp\\skpdi_patch'
# Source location on sunny
patch_store = '\\\sunny\\builds\\odsxp\\'
# Directory with actual patch data
patch_dir = patch_store + patch_num

''' Linux stuff '''
# SSH key location
linux_key_path = 'C:\Users\daniil.aksenov\Documents\ssh\id_rsa.key'
# SSH key prepared for paramiko
linux_key = paramiko.RSAKey.from_private_key_file( linux_key_path )
# SSH user
ssh_user = 'ansible'
# SSH Port
ssh_port = 22

# Tomcat version and path
tomcat_name = 'apache-tomcat-8.5.8'
app_path = '/u01/' + tomcat_name + '/webapps'

''' Переменные. Конец.'''

''' Внутренние функции. Начало. ''' 
def md5_check( checked_file ):
    '''Internal function to check files md5'''
    md5sum = hashlib.md5(open(checked_file,'rb').read()).hexdigest()
    return md5sum

def linux_exec( linux_host, shell_command ):
    '''Internal function for linux commands remote execution'''
       
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect( hostname = linux_host, username = ssh_user, port = ssh_port, pkey = linux_key )
    
    stdin, stdout, stderr = client.exec_command( shell_command )
    data = stdout.read() + stderr.read()
    client.close()
    return data
    
def linux_put( linux_host, source_path, dest_path ):
    '''Internal function for to_linux file copy'''
           
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
Копируем папку с необхоидмым патчем с Sunny.
'''
# Purge previous patches from stage directory. TODO: Redo it in python only w/o call.
call( [ 'rmdir', stage_dir, '/s', '/q' ], shell=True )
call( [ 'md', stage_dir ], shell=True )

# Это нужно убрать. патчи будут копироваться только в случае необходимости.
#print "Copying patch data from SUNNY."
#call( [ 'xcopy', '/e', patch_dir, stage_dir ], shell=True )

'''
Блок установки патчей БД.
Подключаемся к БД и вытаскиваем номера уже устаноленных патей.
'''
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

''' Берем список БД патчей из директории с патчами '''
patches_targ = [ name for name in listdir( patch_dir + '\\patches' ) ]

'''Сравненеие уже установленных патчей с патчами из директории.
Если версия на БД установлено меньше чем лежит в директории с патчами, устанавливаем недостающие патчи.
Во всех остальных случаях - пропускаем этот блок.'''
print "Checking database patch level:\n"
if max(patches_targ) == max(patches_curr):
    print "\tNo database patches required.\n"
elif max(patches_targ) > max(patches_curr):
    print "\tDatabase needs patching.\n"
    patches_miss = []
    for i in (set(patches_targ) - set(patches_curr)):
        if i > max(patches_curr):
            patches_miss.append(i)

    # Copy patch installer to needed folders.
    print "Following database patches will be applied: " + ', '.join(patches_miss)
    for i in patches_miss:
        # Copy missing db patches from SUNNY.
        call( [ 'xcopy', '/e', patch_dir + '\\patches' + i, stage_dir + '\\patches\\' + i  ], shell=True )
        # Copy dbpatch installer to parch directories.
        call( [ 'copy', '/y', 'C:\\Users\\daniil.aksenov\\Documents\\GitHub\\work\\skpdi\\patching\\' + db_patch_file , stage_dir + '\\patches\\' + i ], shell=True )

    # Stop tomcats.
    linux_exec( application_host, 'sudo systemctl stop tomcat' )
    # Install needed db patches.
    # Sorted to run in order, cwd require to run in cpecific dir.
    for i in sorted(patches_miss):
        call( [ stage_dir + '\\patches\\' + i + '\\' + db_patch_file ], shell=True, cwd = stage_dir + '\\patches\\' + i)
    # TODO: database patches log.
else:
    print 'ERROR: Something wrong with database patching.'
    
'''
Блок обновления приложения.
'''
# Ключи разные для paramiko и pscp? или можно будет взять один?
# Переименовать war файл из патчевого в целевой.
# Это убрать вообще. Сравнивать и копировать будем с Synny
#call( [ 'ren', '*.war', war_name ], shell = True, cwd = stage_dir)

# glob search returns array, so need to add [0] into md5_check
# Path to source *.war file on Sunny.
print "Checking java application version:\n"
war_path = glob( patch_dir + '\\*.war')[0]
source_md5 = md5_check( war_path )
target_md5 = linux_exec( application_host, 'sudo md5sum ' + app_path + '/' + war_name )

# Need to split result cos on linux :e00930ce2184b11c804ae84a49955a36  /u01/apache-tomcat-8.5.8/webapps/demo.war
if source_md5 == target_md5.split(" ")[0]: 
   print "\tNo application update required.\n"
   exit()
else:
   print "\tJava application will be updated.\n"

# Учесть последовательное выполнение для 2 и более хостов приложений
linux_exec( application_host, 'rm -rf /tmp/webapps && mkdir /tmp/webapps' )
print "Copying " + war_path + " to " + application_host + ":/tmp/webapps/"
linux_put( application_host, war_path, '/tmp/webapps/' + war_name )
linux_exec( application_host, 'sudo chown tomcat.tomcat /tmp/webapps/' + war_name )

# Ensure tomcat stopped.
print "Stopping application servers...."
cmd_result = linux_exec( application_host, 'sudo systemctl stop tomcat' )

# Remove old app files and dirs. Add app path.
linux_exec( application_host, 'sudo rm ' + app_path + '/' + war_name )
linux_exec( application_host, 'sudo rm -rf ' + app_path + '/' + war_fldr )
# Copy applicateion *.war file to tomcat dir.
linux_exec( application_host, 'sudo cp /tmp/webapps/' + war_name + ' ' + app_path + '/' + war_name )


# Check copied files md5. To be compared with source.
# md5sum %app_name%.war
target_md5 = linux_exec( application_host, 'sudo md5sum ' + app_path + '/' + war_name )

if source_md5 == target_md5.split(" ")[0]:
   print 'Application version matches ' + patch_num 
else:
   print 'ERROR: Application version not matches ' + patch_num

# Start tomcat.
linux_exec( application_host, 'sudo systemctl start tomcat' )
# Check tomcat after starting.
linux_exec( application_host, 'sudo systemctl status tomcat' )