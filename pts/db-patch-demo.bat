@echo off
chcp 65001

rem Тестовый контур ФОРС
set PGHOST=172.29.7.11
set PGPORT=5432

set PGUSER=pts
set PGDATABASE=pts_show
set PGPASSWORD=pts

echo Connecting to %PGDATABASE%@%PGHOST%:%PGPORT%

pause

psql <install.sql >install.log 2>&1
