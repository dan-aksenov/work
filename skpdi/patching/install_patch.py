from subprocess import call
from sys import argv
# for db connection
from psycopg2 import connect
from os import listdir
# for ssh connection.
import paramiko
# for file md5s
import hashlib

''' Переменные. Начало. '''
# Номер патча из первого параметра:
patch_num = argv[1]
# Целевой контур prod или demo из второго параметра.
target = argv[2]
if target == 'demo':
    application_host = 'gudhskpdi-test-app'
	war_name = 'demo'
	db_patch_file = 'db_patch_demo.bat'
	db_name = 'ods_demo'
	db_host = 'gudhskpdi-db-test'
	
# Stage dir to hold patch data.
stage_dir = 'd:\\tmp\\skpdi_patch'
# Source location on sunny
patch_store = '\\\sunny\\builds\\odsxp\\'
# Directory with actual patch data
patch_dir = patch_store + patch_num
# Linux key
linux_key = 'C:\Users\daniil.aksenov\Documents\ssh\id_rsa.'
tomcat_name = 'apache-tomcat-8.5.8'
app_path = '/u01/' + tomcat_name + '/webapps'
''' Переменные. Конец.'''

''' Внутренние функции. Начало. ''' 
def md5_check( checked_file ):
    '''Ingernal function to check files md5'''
	md5sum = hashlib.md5(open(checked_file,'rb').read()).hexdigest()
	return md5sum

def linux_exec( linux_host, shell_command ):
	'''Ingernal function for linux commands remote execution'''
	host = linux_host
	user = 'ansible'
	ssh_key = paramiko.RSAKey.from_private_key_file(linux_key + 'key')
	port = 22
	client = paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(hostname=host, username=user, port = port, pkey = ssh_key)
	stdin, stdout, stderr = client.exec_command( shell_command )
	data = stdout.read() + stderr.read()
	client.close()
	return data
''' Внутренние функции. Конец. '''
	
'''
Блок подготовки.
Копируем папку с необхоидмым патчем с Sunny.
'''
# Purge previous patches from stage directory. TODO: Redo it in python only w/o call.
call( [ 'rmdir', stage_dir, '/s', '/q' ], shell=True )
call( [ 'md', stage_dir ], shell=True )
# Copy patch from storage. TODO: Redo it in python only w/o call.
call( [ 'xcopy', '/e', patch_dir, stage_dir ], shell=True )

'''
Блок установки патчей БД.
Подключаемся к БД и вытаскиваем номера уже устаноленных патей.
'''
conn_string = 'dbname= '' + db_name + '' user='ods' password='ods' host='' + db_host + '''
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

'''Берем список БД патчей из директории с патчами'''
patches_targ = [ name for name in listdir( patch_dir + '\\patches' ) ]

'''Сравненеие уже установленных патчей с патчами из директории.
Если версия на БД установлено меньше чем лежит в директории с патчами, устанавливаем недостающие патчи.
Во всех остальных случаях - пропускаем этот блок.'''
if max(patches_targ) == max(patches_curr):
    print 'No database patches required.'
elif max(patches_targ) > max(patches_curr):
    patches_miss = []
    for i in (set(patches_targ) - set(patches_curr)):
        if i > max(patches_curr):
            patches_miss.append(i)

	# Copy patch installer to needed folders.
    for i in patches_miss:
        call( [ 'copy', '/y', 'C:\\Users\\daniil.aksenov\\Documents\\GitHub\\work\\skpdi\\patching\\' + db_patch_file , stage_dir + '\\patches\\' + i ], shell=True )

    # Stop tomcats.
    linux_exec( application_host, 'sudo systemctl stop tomcat' )
    # Install needed db patches.
    # Sorted to run in order. cwd require to run in cpecific dir.
    for i in sorted(patches_miss):
        call( [ stage_dir + '\\patches\\' + i + '\\' + db_patch_file ], shell=True, cwd = stage_dir + '\\patches\\' + i)
    # TODO database patches log.
else:
    print 'Something wrong.'
	
'''
Блок обновления приложения.
'''
# Ключи разные для paramiko и pscp? или можно будет взять один?
# Переименовать war файл из патчевого в целевой.
call( [ 'ren', '*.war', war_name + '.war' ] shell = True, cwd = stage_dir)
soruce_md5 = md5_check( stage_dir + '\\' + war_name + '.war' )


# Учесть последовательное выполнение для 2 и более хостов приложений
linux_exec( application_host, 'rm -rf /tmp/webapps && mkdir /tmp/webapps' )
call( [ 'pscp', '-i', linux_key + 'ppk', war_name + '.war', 'ansible@' + application_host + ':/tmp/webapps' ], shell = True, cwd = stage_dir )
linux_exec( application_host, 'sudo chown tomcat.tomcat /tmp/webapps/' + war_name )

# Ensure tomcat stopped.
linux_exec( application_host, 'sudo systemctl stop tomcat' )

# Remove old app files and dirs. Add app path.
linux_exec( application_host, 'sudo rm ' + app_path + '/' + war_name + '.war -f' )
linux_exec( application_host, 'sudo rm ' + app_path + '/' + war_name + ' -rf' )
linux_exec( application_host, 'sudo mv /tmp/webapps/' + war_name + '. war + ' app_path + '/' )

# Check copied files md5. To be compared with source.
# md5sum %app_name%.war
target_md5 = linux_exec( application_host, ' md5sum ' + app_path + '/' + war + '.war' )

# Start tomcat.
linux_exec( application_host, 'sudo systemctl start tomcat' )
# Check tomcat after starting.
linux_exec( application_host, 'sudo systemctl status tomcat' )