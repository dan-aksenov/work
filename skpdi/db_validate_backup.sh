# Move to staging directory.
STAGE_DIR=/usr/local/pgsql/basebackup
# Directory containing pg_basebackup should be copied here like $STAGE_DIR/db-09-22-2017_09
STAGE_DATA=db-09-24-2017_00

cd $STAGE_DIR

# Untar main backup archive.
tar xvf $STAGE_DIR/$STAGE_DATA/base.tar -C $STAGE_DIR/$STAGE_DATA

# Make directories to create tablespaces.
mkdir ./tablespace
cd ./tablespace
mkdir fdc_log_tab fdc_nsi_tab fdc_ods_big_tab fdc_ods_ind fdc_parameter_ind fdc_secr_ind
mkdir fdc_log_ind fdc_nsi_ind fdc_ods_big_ind fdc_ods_geo_ind fdc_ods_tab fdc_secr_tab fdc_parameter_tab

# Use this query on original DB to generate move command for tablespace archives.
# select 'mv '|| oid || '.tar $STAGE_DIR/tablespace/'||spcname from pg_tablespace;

# Move tablespace archives to destinagion direcrories.
mv $STAGE_DIR/$STAGE_DATA/129717.tar $STAGE_DIR/tablespace/fdc_log_ind/
mv $STAGE_DIR/$STAGE_DATA/129718.tar $STAGE_DIR/tablespace/fdc_log_tab/ 
mv $STAGE_DIR/$STAGE_DATA/129719.tar $STAGE_DIR/tablespace/fdc_nsi_ind/ 
mv $STAGE_DIR/$STAGE_DATA/129720.tar $STAGE_DIR/tablespace/fdc_nsi_tab/ 
mv $STAGE_DIR/$STAGE_DATA/129721.tar $STAGE_DIR/tablespace/fdc_ods_big_ind/
mv $STAGE_DIR/$STAGE_DATA/129722.tar $STAGE_DIR/tablespace/fdc_ods_big_tab/ 
mv $STAGE_DIR/$STAGE_DATA/129723.tar $STAGE_DIR/tablespace/fdc_ods_geo_ind/ 
mv $STAGE_DIR/$STAGE_DATA/129724.tar $STAGE_DIR/tablespace/fdc_ods_ind/ 
mv $STAGE_DIR/$STAGE_DATA/129725.tar $STAGE_DIR/tablespace/fdc_ods_tab/ 
mv $STAGE_DIR/$STAGE_DATA/181169.tar $STAGE_DIR/tablespace/fdc_secr_ind/
mv $STAGE_DIR/$STAGE_DATA/181170.tar $STAGE_DIR/tablespace/fdc_secr_tab/
mv $STAGE_DIR/$STAGE_DATA/181171.tar $STAGE_DIR/tablespace/fdc_parameter_ind/
mv $STAGE_DIR/$STAGE_DATA/181172.tar $STAGE_DIR/tablespace/fdc_parameter_tab/

# Untar tablespace archives.
for i in $(ls $STAGE_DIR/tablespace)
do
find $STAGE_DIR/tablespace/$i -name '*.tar' -exec tar xvf "{}" -C $STAGE_DIR/tablespace/$i \;
done

# Edit postgresql.conf. Restrict listener and change active port.
sed -i 's/listen_addresses/#listen_addresses/g' $STAGE_DIR/$STAGE_DATA/postgresql.conf
sed -i 's/port = 5432/port = 54320/g' $STAGE_DIR/$STAGE_DATA/postgresql.conf

# Relink tablespace links with python script. to be provided.
TABLESPACE_LINKS=$STAGE_DIR/$STAGE_DATA/pg_tblspc

ln -sf $STAGE_DIR/tablespace/fdc_log_ind $TABLESPACE_LINKS/129717
ln -sf $STAGE_DIR/tablespace/fdc_log_tab $TABLESPACE_LINKS/129718
ln -sf $STAGE_DIR/tablespace/fdc_nsi_ind $TABLESPACE_LINKS/129719
ln -sf $STAGE_DIR/tablespace/fdc_nsi_tab $TABLESPACE_LINKS/129720
ln -sf $STAGE_DIR/tablespace/fdc_ods_big_ind $TABLESPACE_LINKS/129721
ln -sf $STAGE_DIR/tablespace/fdc_ods_big_tab $TABLESPACE_LINKS/129722
ln -sf $STAGE_DIR/tablespace/fdc_ods_geo_ind $TABLESPACE_LINKS/129723
ln -sf $STAGE_DIR/tablespace/fdc_ods_ind $TABLESPACE_LINKS/129724
ln -sf $STAGE_DIR/tablespace/fdc_ods_tab $TABLESPACE_LINKS/129725
ln -sf $STAGE_DIR/tablespace/fdc_secr_ind $TABLESPACE_LINKS/181169
ln -sf $STAGE_DIR/tablespace/fdc_secr_tab $TABLESPACE_LINKS/181170
ln -sf $STAGE_DIR/tablespace/fdc_parameter_ind $TABLESPACE_LINKS/181171
ln -sf $STAGE_DIR/tablespace/fdc_parameter_tab $TABLESPACE_LINKS/181172

# Attempt start. This time this'll do.
pg_ctl -D $STAGE_DIR/$STAGE_DATA start

# Read log to be shure DB is starged.
DOW=$(date --date=${dateinfile#?_} "+%A"|cut -c -3)
tail $STAGE_DIR/$STAGE_DATA/pg_log/postgresql-$DOW.log