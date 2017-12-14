set dbname=%1

set db_dest=-U postgres -h gudhskpdi-db-test
set db_src=-U postgres -h gudhskpdi-db-01

echo Reimporting %dbname% database.
REM create temprorry database
psql %db_dest% -c "create database %dbname%_tmp with owner ods" postgres
pause

REM Direct network import database. Exclude event log and parameters data.
pg_dump %db_src% -Fp -v --exclude-table-data "event.fdc_app_log_*" --exclude-table-data "parameter.fdc_parameter_md" ods_prod | psql %db_dest% %dbname%_tmp
pause

REM Reimport parameter_md.
pg_dump %db_dest% -Fp -t "parameter.fdc_parameter_md" %dbname% | psql %db_dest% %dbname%_tmp
pause

REM Rename database.
psql %db_dest% -c "update pg_database set datallowconn = false where datname = '%dbname%'"
psql %db_dest% -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '%dbname%'"
psql %db_dest% -c "alter database %dbname% rename to %dbname%_old"
pause

psql %db_dest% -c "update pg_database set datallowconn = false where datname = '%dbname%_tmp'"
psql %db_dest% -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '%dbname%_tmp'"
psql %db_dest% -c "alter database %dbname%_tmp rename to %dbname%"
pause

REM Drop old database
psql %db_dest% -c "update pg_database set datallowconn = false where datname = '%dbname%_old"
psql %db_dest% -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '%dbname%_old'"
psql %db_dest% -c "drop database %dbname%_old"
pause

REM Allow connections.
psql %db_dest% -c "update pg_database set datallowconn = true where datname = '%dbname%'"
pause