@chcp 65001
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
REM UPDATE PredProd skpdi server.
set PGHOST=10.139.127.9

set PGPORT=5432
set PGUSER=ods
set PGPASSWORD=ods
set PGDATABASE=ods_demo

set script_name=install_db
set width=120
set height=60
mode con:cols=%width% lines=%height%

set "bat_name=%~n0"
set "bat_path=%~dp0"
set "run_path=%bat_path%"

cd %run_path%

set "spool_file=%run_path%%script_name%_log.log"
set "run_file=%run_path%%script_name%.sql"

rem Запуск
psql <%run_file% >%spool_file% 2>&1

exit