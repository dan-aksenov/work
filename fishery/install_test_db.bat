@chcp 65001
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

rem DEV:
REM set PGHOST=fishery-dev-db.fors.ru

rem TEST:
set PGHOST=fishery-test-db.fors.ru

rem TEST ЦОД:
rem set PGHOST=62.61.18.14

set PGPORT=5432
set PGUSER=fishery
set PGPASSWORD=fishery
set PGDATABASE=fishery
 
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
set "load_file=%run_path%/load/test_csv_file.csv"
rem Запуск
psql <%run_file% >%spool_file% 2>&1

exit