src_host=gudhskpdi-db-01

echo Dump and download ODS_PROD database.
time ssh $src_host sudo -u postgres pg_dump ods_prod -Fc -Z5 --exclude-table-data "event.fdc_app_log_*" --exclude-table-data "parameter.fdc_parameter_md" -f /backup/dump/prod.dmp
time scp $src_host:/backup/dump/prod.dmp /tmp/