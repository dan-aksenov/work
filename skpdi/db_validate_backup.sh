# Basebackup storage.
BACKUP_DIR=/mnt/nfs/backup
# Get latest backup.
CURRENT_BACKUP=$(ls -t $BACKUP_DIR | grep db | head -1)
# Directory where backup will be tested.
STAGE_DIR=/usr/local/pgsql/backup_test

mkdir $STAGE_DIR
cd $STAGE_DIR
# Copy backup from storage.
cp $BACKUP_DIR/$CURRENT_BACKUP $STAGE_DIR -r

# Untar main backup archive.
# Backups changed to plain. Thus commented out.
#tar xvf $STAGE_DIR/$CURRENT_BACKUP/base.tar -C $STAGE_DIR/$CURRENT_BACKUP

# Tablespace section not needed anymore. But let in remain here just as example of psql - bash variable passing and execution.
# Make directories to hold tablespaces.
#mkdir $STAGE_DIR/tablespace
#cd $STAGE_DIR/tablespace
# Create tablespace subdirs.
#psql -t ods_prod -c "select 'mkdir $STAGE_DIR/tablespace/'||spcname from pg_tablespace where spcname not in ('pg_default','pg_global')" | /bin/bash
# Move tablespace archives to destinagion direcrories.
#psql -t ods_prod -c "select 'mv $STAGE_DIR/$CURRENT_BACKUP/'|| oid || '.tar $STAGE_DIR/tablespace/'||spcname from pg_tablespace where spcname not in ('pg_default','pg_global')" | /bin/bash
# Untar tablespace archives.
#for i in $(ls $STAGE_DIR/tablespace)
#do
#find $STAGE_DIR/tablespace/$i -name '*.tar' -exec tar xvf "{}" -C $STAGE_DIR/tablespace/$i \;
#done
# End of Tablespace section.

# Edit postgresql.conf. Restrict listener and change active port.
sed -i 's/listen_addresses/#listen_addresses/g' $STAGE_DIR/$CURRENT_BACKUP/postgresql.conf
sed -i 's/port = 5432/port = 54320/g' $STAGE_DIR/$CURRENT_BACKUP/postgresql.conf
# Archive command not needed.
sed -i 's/archive_command/#archive_command/g' $STAGE_DIR/$CURRENT_BACKUP/postgresql.conf

# Add restore arhivelogs from backup.
cat >> $STAGE_DIR/$CURRENT_BACKUP/recovery.conf <<EOF
restore_command = 'gunzip < $BACKUP_DIR/pg_archive/%f > "%p"'
recovery_target_timeline = 'latest'
EOF

# Relink tablespace links with python script. to be provided.
#TABLESPACE_LINKS=$STAGE_DIR/$CURRENT_BACKUP/pg_tblspc
#psql -t ods_prod -c "select 'ln -sf $STAGE_DIR/tablespace/'|| spcname || ' $TABLESPACE_LINKS/'|| oid from pg_tablespace where spcname not in ('pg_default','pg_global')" | /bin/bash

# Create log folder.
mkdir $STAGE_DIR/$CURRENT_BACKUP/pg_log

# Reset xlog.
#pg_resetxlog -f $STAGE_DIR/$CURRENT_BACKUP

# Attempt start.
pg_ctl -w -D $STAGE_DIR/$CURRENT_BACKUP start

psql -p 54320 ods_prod -c "select a.datetime from event.fdc_app_log a order by datetime desc limit 1"
# Read log to be shure DB is starged.
DOW=$(date --date=${dateinfile#?_} "+%A"|cut -c -3)
tail $STAGE_DIR/$CURRENT_BACKUP/pg_log/postgresql-$DOW.log

cp $STAGE_DIR/$CURRENT_BACKUP/pg_log/postgresql-$DOW.log /tmp/restore.log

#pg_ctl -D $STAGE_DIR/$CURRENT_BACKUP stop

#rm -rf $STAGE_DIR/*
