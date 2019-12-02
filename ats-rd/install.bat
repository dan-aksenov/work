@echo off
chcp 65001

rem Контур разработки
set PGHOST=ats-rd.fors.ru
rem set PGPORT=5432

set PGUSER=postgres
set PGDATABASE=ats_test
set PGPASSWORD=postgres

echo Connecting to %PGDATABASE%@%PGHOST%:%PGPORT%

pause

psql <install.sql >install.log 2>&1
