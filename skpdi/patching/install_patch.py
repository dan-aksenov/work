from subprocess import call
from sys import argv
from psycopg2 import connect
from os import listdir

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
a = []
for patch in patches_curr:
    i = patch.split('_')[1]
    a.append(i)	 

b = []
for patch in patches_targ:
    i = patch.split('_')[1]
    b.append(i)

list(set(b) - set(a))
'''
В настоящее время возвращает 6 патчей, которые есть в файлах, но нет в БД
In [139]: list(set(b) - set(a))
Out[139]: ['0000', '0068a', '0101', '0092c', '0076', '0094a']
Может следует сравнивать только последние Х, или чтото в этом роде.
'''
	
# Copy patch installer to needed folders.

# not working yet.
call ( [ "for /D %a in ('d:\skpdi_patch\patches\*') do xcopy /y /d db_patch_%1.bat '%a\'" ] )
# Stop tomcats.
# pssh

# Install needed patches.
# run bat files	

# 3. Install app patches
# pssh
 