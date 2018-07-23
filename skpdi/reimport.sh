# Variables to be passed from uper script.
# export dbname=$1
# export db_dest=-U postgres -p 5432 -h skpdi-test-db
# export db_src=-U postgres -h gudhskpdi-db-01

echo ###################################################################################
echo Create temporary database ${dbname}_tmp
psql $db_dest -c "create database ${dbname}_tmp with owner ods" postgres
psql $db_dest -c "select datname, (pg_stat_file('base/'||oid||'/PG_VERSION')).modification AS datcreated from pg_database where datname = '${dbname}_tmp'"
read -p "Press [Enter] key to proceed..."
echo ###################################################################################
echo Import source ODS_PROD database to ${dbname}_tmp. Exclude event log and parameters data.
pg_dump $db_src -Fp -v --exclude-table-data "event.fdc_app_log_*" --exclude-table-data "parameter.fdc_parameter_md" ods_prod > /tmp/$dbname.sql
psql $db_dest -f /tmp/$dbname.sql ${dbname}_tmp 2>/tmp/${dbname}_import.log
read -p "Press [Enter] key to proceed..."
echo ###################################################################################
echo Reimport parameter_md from old db
pg_dump $db_dest -Fp -t "parameter.fdc_parameter_md" $dbname | psql $db_dest ${dbname}_tmp
read -p "Press [Enter] key to proceed..."
echo ###################################################################################
echo Rename database $dbname to ${dbname}_old
psql $db_dest -c "update pg_database set datallowconn = false where datname = '$dbname'"
psql $db_dest -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '$dbname'"
psql $db_dest -c "alter database $dbname rename to ${dbname}_old"
read -p "Press [Enter] key to proceed..."
echo ###################################################################################
echo Rename database ${dbname}_tmp to $dbname
psql $db_dest -c "update pg_database set datallowconn = false where datname = '${dbname}_tmp'"
psql $db_dest -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '${dbname}_tmp'"
psql $db_dest -c "alter database ${dbname}_tmp rename to $dbname"
read -p "Press [Enter] key to proceed..."
echo ###################################################################################
echo Allow connections to $dbname
psql $db_dest -c "update pg_database set datallowconn = true where datname = '$dbname'"
psql $db_dest -c "select datallowconn from pg_database where datname = '$dbname'"

echo ###################################################################################
echo Drop old database ${dbname}_old? Or CTRL+C to exit batch
read -p "Press [Enter] key to proceed..."
psql $db_dest -c "update pg_database set datallowconn = false where datname = '${dbname}_old'"
psql $db_dest -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '${dbname}_old'"
psql $db_dest -c "drop database ${dbname}_old"
