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
tar xvf $STAGE_DIR/$CURRENT_BACKUP/base.tar -C $STAGE_DIR/$CURRENT_BACKUP

# Edit postgresql.conf. Restrict listener and change active port.
sed -i 's/listen_addresses/#listen_addresses/g' $STAGE_DIR/$CURRENT_BACKUP/postgresql.conf
sed -i 's/port = 5432/port = 54320/g' $STAGE_DIR/$CURRENT_BACKUP/postgresql.conf
# Archive command not needed.
sed -i 's/archive_command/#archive_command/g' $STAGE_DIR/$CURRENT_BACKUP/postgresql.conf
# Add restore arhivelogs from backup.
cat >> $STAGE_DIR/$CURRENT_BACKUP/recovery.conf <<EOF
restore_command = 'cp $BACKUP_DIR/pg_archive/%f "%p"'
recovery_target_timeline = 'latest'
EOF

# Create log folder.
mkdir $STAGE_DIR/$CURRENT_BACKUP/pg_log
# Reset xlog. where to?
pg_resetxlog -f $STAGE_DIR/$CURRENT_BACKUP
# Attempt start.
pg_ctl -w -D $STAGE_DIR/$CURRENT_BACKUP start

psql -p 54320 ods_prod -c "select a.datetime from event.fdc_app_log a order by datetime desc limit 1"
 
# Read log to be shure DB is starged.
DOW=$(date --date=${dateinfile#?_} "+%A"|cut -c -3)
tail $STAGE_DIR/$CURRENT_BACKUP/pg_log/postgresql-$DOW.log

cp $STAGE_DIR/$CURRENT_BACKUP/pg_log/postgresql-$DOW.log /tmp/restore.log

pg_ctl -D $STAGE_DIR/$CURRENT_BACKUP stop

rm -rf $STAGE_DIR/*
