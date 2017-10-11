@chcp 65001
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
REM UPDATE Skpdi server.

REM plink command to stop application servers beroure.
set ssh_key=C:\Users\daniil.aksenov\Documents\ssh\id_rsa.ppk
set usr_nix=ansible
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%
set dst_host=gudhskpdi-app-01
%plink_cmd% "sudo systemctl stop tomcat"

REM Set database's host from first parameter.
SET PGHOST=gudhskpdi-db-test

set PGPORT=5432
set PGUSER=ods
set PGPASSWORD=ods

REM Set database name from second parameter
set PGDATABASE=ods_demo

set script_name=install_db
rem set width=120 Removed to prevent far resizing
rem set height=60
rem mode con:cols=%width% lines=%height%

set "bat_name=%~n0"
set "bat_path=%~dp0"
set "run_path=%bat_path%"

cd %run_path%

set "spool_file=%run_path%%script_name%_log.log"
set "run_file=%run_path%%script_name%.sql"

rem Запуск
psql <%run_file% >%spool_file% 2>&1

psql -c "DELETE FROM core.fdc_sys_class_impl_lnk;"
psql -c "DELETE FROM core.fdc_sys_class_impl;"
psql -c "DELETE FROM core.fdc_sys_class_panel_lnk;"
psql -c "DELETE FROM core.fdc_sys_class_panel;"

type %spool_file%
