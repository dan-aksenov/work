@ECHO OFF
@REM Variables to be passed from uper script.
@REM set dbname=%1
@REM set db_dest=-U postgres -p 5432 -h skpdi-test-db
@REM set db_src=-U postgres -h gudhskpdi-db-01

echo ###################################################################################
echo Create temporary database %dbname%_tmp
psql %db_dest% -c "create database %dbname%_tmp with owner ods" postgres

echo ###################################################################################
echo Import source ODS_PROD database to %dbname%_tmp. Exclude event log and parameters data.
pause
pg_dump %db_src% -Fp -v --exclude-table-data "event.fdc_app_log_*" --exclude-table-data "parameter.fdc_parameter_md" ods_prod > d:/tmp/%dbname%.sql
psql %db_dest% -f d:/tmp/%dbname%.sql %dbname%_tmp 2>d:/tmp/%dbname%_import.log

echo ###################################################################################
echo Reimport parameter_md from old db
pause
pg_dump %db_dest% -Fp -t "parameter.fdc_parameter_md" %dbname% | psql %db_dest% %dbname%_tmp

echo ###################################################################################
echo Rename database %dbname% to %dbname%_old
pause
psql %db_dest% -c "update pg_database set datallowconn = false where datname = '%dbname%'"
psql %db_dest% -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '%dbname%'"
psql %db_dest% -c "alter database %dbname% rename to %dbname%_old"

echo ###################################################################################
psql %db_dest% -c "update pg_database set datallowconn = false where datname = '%dbname%_tmp'"
psql %db_dest% -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '%dbname%_tmp'"
psql %db_dest% -c "alter database %dbname%_tmp rename to %dbname%"

echo ###################################################################################
echo Allowing connections to %dbname%
psql %db_dest% -c "update pg_database set datallowconn = true where datname = '%dbname%'"
psql %db_dest% -c "select datallowconn from pg_database where datname = '%dbname%'"

echo ###################################################################################
echo Drop old database %dbname%_old? Or CTRL+C to exit batch
pause
psql %db_dest% -c "update pg_database set datallowconn = false where datname = '%dbname%_old'"
psql %db_dest% -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '%dbname%_old'"
psql %db_dest% -c "drop database %dbname%_old"
pause
