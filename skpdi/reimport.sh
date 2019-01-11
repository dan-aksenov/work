# Variables to be passed from uper script.
export dbname=$1
export dst_host=$2
export db_dest="-U postgres -p 5432 -h $dst_host"

echo Create temporary database ${dbname}_tmp
psql $db_dest -c "create database ${dbname}_tmp with owner ods" postgres
psql $db_dest -c "select datname, pg_size_pretty(pg_catalog.pg_database_size(datname)) AS Size, (pg_stat_file('base/'||oid||'/PG_VERSION')).modification AS datcreated from pg_database where datname = '${dbname}_tmp'"

read -p "Press [Enter] key import source ODS_PROD database to ${dbname}_tmp. Exclude event log and parameters data."
echo Import source ODS_PROD database to ${dbname}_tmp. Exclude event log and parameters data.
time pg_restore $db_dest --jobs=4 -d ${dbname}_tmp /tmp/prod.dmp 2>/tmp/${dbname}_import.log
psql $db_dest -c "select datname, pg_size_pretty(pg_catalog.pg_database_size(datname)) AS Size, (pg_stat_file('base/'||oid||'/PG_VERSION')).modification AS datcreated from pg_database where datname = '${dbname}_tmp'"

read -p "Press [Enter] key to reimport parameter_md from old db and reset admin password"
pg_dump $db_dest -Fp --data-only -t "parameter.fdc_parameter_md" $dbname | psql $db_dest ${dbname}_tmp
psql $db_dest -c "UPDATE secr.fdc_user_md SET passwd = '$2a$10$GwiQ4p7I6Si/Cr5LJN60duTrpjGVsTFn47ELx1kbRW7RPUD6ucuqy' WHERE sysname = 'ADMIN'" ${dbname}_tmp

read -p "Press [Enter] key to rename database $dbname to ${dbname}_old"
psql $db_dest -c "update pg_database set datallowconn = false where datname = '$dbname'"
psql $db_dest -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '$dbname'"
psql $db_dest -c "alter database $dbname rename to ${dbname}_old"

read -p "Press [Enter] key to rename database ${dbname}_tmp to $dbname"
psql $db_dest -c "update pg_database set datallowconn = false where datname = '${dbname}_tmp'"
psql $db_dest -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '${dbname}_tmp'"
psql $db_dest -c "alter database ${dbname}_tmp rename to $dbname"
psql $db_dest -c "update pg_database set datallowconn = true where datname = '$dbname'"
psql $db_dest -c "select datname, pg_size_pretty(pg_catalog.pg_database_size(datname)) AS Size, (pg_stat_file('base/'||oid||'/PG_VERSION')).modification AS datcreated from pg_database where datname = '${dbname}'"

read -p "Press [Enter] to drop old database ${dbname}_old or CTRL+C to exit batch"
psql $db_dest -c "update pg_database set datallowconn = false where datname = '${dbname}_old'"
psql $db_dest -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '${dbname}_old'"
psql $db_dest -c "drop database ${dbname}_old"