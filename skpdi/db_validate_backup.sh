# Basebackup storage.
BACKUP_DIR=/mnt/nfs/backup
# Get latest backup.
CURRENT_BACKUP=$(ls -t $BACKUP_DIR | head -1)
# Directory where backup will be tested.
STAGE_DIR=/usr/local/pgsql/backup_test

cd $STAGE_DIR
# Copy backup from storage.
cp $BACKUP_DIR/$CURRENT_BACKUP $STAGE_DIR -r

# Untar main backup archive.
tar xvf $STAGE_DIR/$CURRENT_BACKUP/base.tar -C $STAGE_DIR/$CURRENT_BACKUP

# Make directories to hold tablespaces.
mkdir $STAGE_DIR/tablespace
cd $STAGE_DIR/tablespace

# Connect to source DB and get tablespace names.
psql -t ods_prod -c "select 'mkdir $STAGE_DIR/tablespace/'||spcname from pg_tablespace where spcname not in ('pg_default','pg_global')" | /bin/bash
#mkdir fdc_log_tab fdc_nsi_tab fdc_ods_big_tab fdc_ods_ind fdc_parameter_ind fdc_secr_ind
#mkdir fdc_log_ind fdc_nsi_ind fdc_ods_big_ind fdc_ods_geo_ind fdc_ods_tab fdc_secr_tab fdc_parameter_tab

# Use this query on original DB to generate move command for tablespace archives.
psql -t ods_prod -c "select 'mv $STAGE_DIR/$CURRENT_BACKUP/'|| oid || '.tar $STAGE_DIR/tablespace/'||spcname from pg_tablespace where spcname not in ('pg_default','pg_global')" | /bin/bash

# Move tablespace archives to destinagion direcrories.
#mv $STAGE_DIR/$CURRENT_BACKUP/129717.tar $STAGE_DIR/tablespace/fdc_log_ind/
#mv $STAGE_DIR/$CURRENT_BACKUP/129718.tar $STAGE_DIR/tablespace/fdc_log_tab/ 
#mv $STAGE_DIR/$CURRENT_BACKUP/129719.tar $STAGE_DIR/tablespace/fdc_nsi_ind/ 
#mv $STAGE_DIR/$CURRENT_BACKUP/129720.tar $STAGE_DIR/tablespace/fdc_nsi_tab/ 
#mv $STAGE_DIR/$CURRENT_BACKUP/129721.tar $STAGE_DIR/tablespace/fdc_ods_big_ind/
#mv $STAGE_DIR/$CURRENT_BACKUP/129722.tar $STAGE_DIR/tablespace/fdc_ods_big_tab/ 
#mv $STAGE_DIR/$CURRENT_BACKUP/129723.tar $STAGE_DIR/tablespace/fdc_ods_geo_ind/ 
#mv $STAGE_DIR/$CURRENT_BACKUP/129724.tar $STAGE_DIR/tablespace/fdc_ods_ind/ 
#mv $STAGE_DIR/$CURRENT_BACKUP/129725.tar $STAGE_DIR/tablespace/fdc_ods_tab/ 
#mv $STAGE_DIR/$CURRENT_BACKUP/181169.tar $STAGE_DIR/tablespace/fdc_secr_ind/
#mv $STAGE_DIR/$CURRENT_BACKUP/181170.tar $STAGE_DIR/tablespace/fdc_secr_tab/
#mv $STAGE_DIR/$CURRENT_BACKUP/181171.tar $STAGE_DIR/tablespace/fdc_parameter_ind/
#mv $STAGE_DIR/$CURRENT_BACKUP/181172.tar $STAGE_DIR/tablespace/fdc_parameter_tab/

# Untar tablespace archives.
for i in $(ls $STAGE_DIR/tablespace)
do
find $STAGE_DIR/tablespace/$i -name '*.tar' -exec tar xvf "{}" -C $STAGE_DIR/tablespace/$i \;
done

# Edit postgresql.conf. Restrict listener and change active port.
sed -i 's/listen_addresses/#listen_addresses/g' $STAGE_DIR/$CURRENT_BACKUP/postgresql.conf
sed -i 's/port = 5432/port = 54320/g' $STAGE_DIR/$CURRENT_BACKUP/postgresql.conf

# Relink tablespace links with python script. to be provided.
TABLESPACE_LINKS=$STAGE_DIR/$CURRENT_BACKUP/pg_tblspc

psql -t ods_prod -c "select 'ln -sf $STAGE_DIR/tablespace/'|| spcname || ' $TABLESPACE_LINKS/'|| oid from pg_tablespace where spcname not in ('pg_default','pg_global')" /bin/bash

#ln -sf $STAGE_DIR/tablespace/fdc_log_ind $TABLESPACE_LINKS/129717
#ln -sf $STAGE_DIR/tablespace/fdc_log_tab $TABLESPACE_LINKS/129718
#ln -sf $STAGE_DIR/tablespace/fdc_nsi_ind $TABLESPACE_LINKS/129719
#ln -sf $STAGE_DIR/tablespace/fdc_nsi_tab $TABLESPACE_LINKS/129720
#ln -sf $STAGE_DIR/tablespace/fdc_ods_big_ind $TABLESPACE_LINKS/129721
#ln -sf $STAGE_DIR/tablespace/fdc_ods_big_tab $TABLESPACE_LINKS/129722
#ln -sf $STAGE_DIR/tablespace/fdc_ods_geo_ind $TABLESPACE_LINKS/129723
#ln -sf $STAGE_DIR/tablespace/fdc_ods_ind $TABLESPACE_LINKS/129724
#ln -sf $STAGE_DIR/tablespace/fdc_ods_tab $TABLESPACE_LINKS/129725
#ln -sf $STAGE_DIR/tablespace/fdc_secr_ind $TABLESPACE_LINKS/181169
#ln -sf $STAGE_DIR/tablespace/fdc_secr_tab $TABLESPACE_LINKS/181170
#ln -sf $STAGE_DIR/tablespace/fdc_parameter_ind $TABLESPACE_LINKS/181171
#ln -sf $STAGE_DIR/tablespace/fdc_parameter_tab $TABLESPACE_LINKS/181172

# Attempt start.
pg_ctl -D $STAGE_DIR/$CURRENT_BACKUP start

# Read log to be shure DB is starged.
DOW=$(date --date=${dateinfile#?_} "+%A"|cut -c -3)
tail $STAGE_DIR/$CURRENT_BACKUP/pg_log/postgresql-$DOW.log

pg_ctl -D $STAGE_DIR/$CURRENT_BACKUP stop

rm -rf $STAGE_DIR/$CURRENT_BACKUP
rm -rf $STAGE_DIR/tablespace
