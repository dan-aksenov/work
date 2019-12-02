@echo off
chcp 65001

rem Тестовый контур ФОРС
set PGHOST=172.29.7.200
set PGPORT=6432

set PGUSER=pts
set PGDATABASE=pts_bel
set PGPASSWORD=pts

echo Connecting to %PGDATABASE%@%PGHOST%:%PGPORT%

pause

psql <install.sql >install.log 2>&1
