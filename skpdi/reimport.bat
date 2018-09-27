@ECHO OFF
@REM Variables to be passed from uper script.
@REM set dbname=%1
@REM set db_dest=-U postgres -p 5432 -h skpdi-test-db
@REM set db_src=-U postgres -h gudhskpdi-db-01

REM Putty config
set ssh_key=C:\Users\daniil.aksenov\Documents\ssh\id_rsa.ppk
set usr_nix=ansible
set src_host=gudhskpdi-db-01
REM Create plink command for use in script below.
set plink_cmd=plink -i %ssh_key% %usr_nix%@%src_host%
set stage=/backup

echo ###################################################################################
echo Create temporary database %dbname%_tmp
psql %db_dest% -c "create database %dbname%_tmp with owner ods" postgres
psql %db_dest% -t -c "SELECT d.datname AS Name, pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname)) AS Size FROM pg_catalog.pg_database d where d.datname = '%dbname%_tmp'"

echo ###################################################################################
echo Import source ODS_PROD database to %dbname%_tmp. Exclude event log and parameters data.
pause
%plink_cmd% sudo -u postgres pg_dump --format=custom --compress 5 --exclude-table-data "event.fdc_app_log_*" --exclude-table-data "parameter.fdc_parameter_md" --file=%stage%/reimp.dmp ods_prod 
pscp -C -i %ssh_key% %usr_nix%@%src_host%:%stage%/reimp.dmp d:/tmp/reimp.dmp
pg_restore %db_dest% -d %dbname%_tmp -v d:/tmp/reimp.dmp 2>d:/tmp/%dbname%_import.log
psql %db_dest% -t -c "SELECT d.datname AS Name, pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname)) AS Size FROM pg_catalog.pg_database d where d.datname = '%dbname%_tmp'"
echo ###################################################################################
echo Reimport parameter_md from old db
msg %username% Database %1 imported
pause
pg_dump %db_dest% --format plain --data-only -t "parameter.fdc_parameter_md" %dbname% | psql %db_dest% %dbname%_tmp

echo SET password fro admin user
psql %db_dest% -c "UPDATE secr.fdc_user_md SET passwd = '$2a$10$GwiQ4p7I6Si/Cr5LJN60duTrpjGVsTFn47ELx1kbRW7RPUD6ucuqy' WHERE sysname = 'ADMIN'" %dbname%_tmp

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
psql %db_dest% -t -c "SELECT d.datname AS Name, pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname)) AS Size FROM pg_catalog.pg_database d where d.datname = '%dbname%'"
pause
