from subprocess import call
from sys import argv

# for db connection
from psycopg2 import connect
from os import listdir

# for ssh connection. Или взять plink? всеравно для копирования нужен pscp.
import paramico

# Variables:
# Pathc number got from 1st argument
patch_num = argv[1]
# Stage dir to hold patch data.
stage_dir = "d:\\tmp\\skpdi_patch"
# Source location on sunny
patch_store = "\\\sunny\\builds\\odsxp\\"
# Directory with actual patch data
patch_dir = patch_store + patch_num

# Purge previous patches from stage directory. TODO: Redo it in python only w/o call.
call( [ "rmdir", stage_dir, "/s", "/q" ], shell=True )
call( [ "md", stage_dir ], shell=True )

# Copy patch from storage. TODO: Redo it in python only w/o call.
call( [ "xcopy", "/e", patch_dir, stage_dir ], shell=True )

# Get war md5 and store for future compare.

# Get list of needed db patches.
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

# Database patch Directory listing 
patches_targ = [name for name in listdir( patch_dir + '\\patches' )]

# Get missing db patches.
'''
Но на мой взгляд как-то криво. Можно ли сделать проверку один раз, без двух циклов.
На stack overflow правда пишут что решение годное. itertools у меня не получилось, наверное из-за условия булевского i>max(p_curr_num).
'''

patches_miss = []
for i in (set(patches_targ) - set(patches_curr)):
    if i > max(patches_curr):
        patches_miss.append(i)
	
# Copy patch installer to needed folders.

for i in patches_miss:
    call( [ "copy", "/y", "C:\Users\daniil.aksenov\Documents\GitHub\work\skpdi\patching\db_patch_demo.bat", stage_dir + "\\patches\\" + i ], shell=True )

# Stop tomcats. Functionize this! or remake with subprocess call.
host = 'gudhskpdi-test-app'
user = 'ansible'
ssh_key = paramiko.RSAKey.from_private_key_file("C:\Users\daniil.aksenov\Documents\ssh\id_rsa.key")
port = 22

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=host, username=user, password = secret, port = port, pkey = ssh_key)
stdin, stdout, stderr = client.exec_command('sudo systemctl start tomcat')
data = stdout.read() + stderr.read()
client.close()

# Install needed db patches.
# Sorted to run in order. cwd require to run in cpecific dir.
for i in sorted(patches_miss):
    call( [ stage_dir + "\\patches\\" + i + "\\db_patch_demo.bat" ], shell=True, cwd = stage_dir + "\\patches\\" + i)

# TODO database patches log.

# 3. Install app patches
# Ключи разные для paramiko и pscp? или можно будет взять один? Хренова винда!
 call( [ "pscp", "-i", ssh_key, "demo.war", "ansible@gudhskpdi-test-app:/tmp/webapps" ], shell = True, cwd = stage_dir )
