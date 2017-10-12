from subprocess import call
from sys import argv
from psycopg2 import connect

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
cur.execute("""select name from parameter.fdc_patches_log order by id desc limit 1;""")
rows = cur.fetchall()
for row in rows:
    print "   ", row[0]


# Copy patch installer to needed folders.

# Stop tomcats.
# pssh

# Install needed patches.
# run bat files	

# 3. Install app patches
# pssh
 