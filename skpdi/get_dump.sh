# export dbname=$1
# export db_dest=-U postgres -p 5432 -h skpdi-test-db
export db_src='-U postgres -h gudhskpdi-db-01 ods'

echo ###################################################################################
echo Dump and download ODS_PROD database.
pg_dump $db_src -Fp -v --exclude-table-data "event.fdc_app_log_*" --exclude-table-data "parameter.fdc_parameter_md" ods_prod > /tmp/$dbname.sql
echo ###################################################################################