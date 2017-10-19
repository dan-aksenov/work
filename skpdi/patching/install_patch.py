from subprocess import call
from sys import argv

# for db connection
from psycopg2 import connect
from os import listdir

# for ssh connection
import paramico

patch_num = argv[1]
stage_dir = "d:\\tmp\\skpdi_patch"
patch_store = "\\\sunny\\builds\\odsxp\\"
patch_dir = patch_store + patch_num

# Purge previous patches from stage directory. Redo it in python only w/o call.
call( [ "rmdir", stage_dir, "/s", "/q" ], shell=True )
call( [ "md", stage_dir ], shell=True )

# Copy patch from storage. Redo it in python only w/o call.
call( [ "xcopy", "/e", patch_dir, stage_dir ], shell=True )


# 2. Get list of needed db patches
# select name from parameter.fdc_patches_log order by id desc limit 1;

try:
    conn = connect("dbname='ods_prod' user='ods' password='ods' host='10.139.127.2'")
except:
    print "ERROR: unable to connect to the database!"

cur = conn.cursor()
cur.execute("""select name from parameter.fdc_patches_log order by id desc;""")
rows = cur.fetchall()
patches_curr = []
# Transform from tuples to strings to compare with list(set(patches_targ) - set(patches_curr))
for row in rows:
    patches_curr.append(row[0])

# Database patcho Directory listing 
patches_targ = [name for name in listdir( patch_dir + '\\patches' )]

# Get diff. lots of trash!
#list(set(patches_targ) - set(patches_curr))

# Get patch number
'''
Блок ниже не нужен, так как можно сравнивать patches_targ и patches_curr напрямую.
p_curr_num = []
for patch in patches_curr:
    i = patch.split('_')[1]
    p_curr_num.append(i)	 

p_targ_num = []
for patch in patches_targ:
    i = patch.split('_')[1]
    p_targ_num.append(i)

В настоящее время возвращает 6 патчей, которые есть в файлах, но нет в БД
In [139]: list(set(b) - set(a))
Out[139]: ['0000', '0068a', '0101', '0092c', '0076', '0094a']
Может следует сравнивать только последние Х, или чтото в этом роде.

Проблема "вроде как решена" ниже блоком ниже.

for i in (set(p_targ_num) - set(p_curr_num)):
    if i > max(p_curr_num):
        print i

Но на мой взгляд как-то криво. Можно ли сделать проверку один раз, без двух циклов.
На stack overflow правда пишут что решение годное. itertools у меня не получилось, наверное из-за условия булевского i>max(p_curr_num).
'''

patches_miss = []
for i in (set(patches_targ) - set(patches_curr)):
    if i > max(patches_curr):
        patches_miss.append(i)
	
# Copy patch installer to needed folders.

# not working yet.
for i in patches_miss:
    call( [ "copy", "/y", "C:\Users\daniil.aksenov\Documents\GitHub\work\skpdi\patching\db_patch_demo.bat", stage_dir + "\\patches\\" + i ], shell=True )

# Stop tomcats. Functionize this!
host = 'gudhskpdi-test-app'
user = 'ansible'
key = paramiko.RSAKey.from_private_key_file("C:\Users\daniil.aksenov\Documents\ssh\id_rsa.key")
port = 22

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=host, username=user, password = secret, port = port, pkey = key)
stdin, stdout, stderr = client.exec_command('sudo systemctl start tomcat')
data = stdout.read() + stderr.read()
client.close()

# Install needed db patches.
# Sorted 
for i in sorted(patches_miss):
    call( [ stage_dir + "\\patches\\" + i + "\\db_patch_demo.bat" ], shell=True, cwd =  stage_dir + "\\patches\\" + i)


# 3. Install app patches
# pssh