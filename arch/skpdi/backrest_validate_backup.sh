# Directory where backup will be tested.
STAGE_DIR=/usr/local/pgsql/backup_test

mkdir $STAGE_DIR
chmod 700 $STAGE_DIR
cd $STAGE_DIR

echo '##########################################################'
echo Restore started at `date`
pgbackrest --db-path $STAGE_DIR --log-level-console=info --stanza=main restore

# Edit postgresql.conf. Change active port.
sed -i 's/port = 5432/port = 54320/g' $STAGE_DIR/conf.d/25ansible_postgresql.conf
# Archive command not needed.
sed -i 's/archive_command/#archive_command/g' $STAGE_DIR/conf.d/25ansible_postgresql.conf
#Decrease shared buffers
sed -i 's/shared_buffers = .*/shared_buffers = 128MB/g' $STAGE_DIR/conf.d/25ansible_postgresql.conf
sed -i 's/huge_pages = .*/huge_pages = off/g' $STAGE_DIR/conf.d/25ansible_postgresql.conf

# Attempt start.
pg_ctl -w -D $STAGE_DIR start

# Check if db is in recovery/
for i in $(seq 0 100); do
response=$(psql -qAtX -p 54320 -c "SELECT pg_is_in_recovery()::int" -U postgres postgres)
[[ $response == 0 || $i == $try ]] && break
echo "Database is sitll recoverint. "
sleep 60
done

echo '##########################################################'
echo "Restore completed at `date`. Last date from event.fdc_app_log:"
psql --port 54320 --tuples-only ods_predprod --command "select a.datetime from event.fdc_app_log a order by datetime desc limit 1"

DOW=$(date --date=${dateinfile#?_} "+%A"|cut -c -3)
cp $STAGE_DIR/log/postgresql-$DOW.log /tmp/restore.log

echo '##########################################################'
read -p "Press [Enter] to stop test server and delete stage data"

pg_ctl -D $STAGE_DIR stop
rm -rf $STAGE_DIR/*