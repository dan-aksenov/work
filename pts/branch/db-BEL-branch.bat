@echo off
chcp 65001

rem Тестовый контур ФОРС
set PGHOST=172.19.1.127
set PGPORT=5432

set PGUSER=pts
set PGDATABASE=pts_bel_branch
set PGPASSWORD=pts

echo Connecting to %PGDATABASE%@%PGHOST%:%PGPORT%

pause

psql <install.sql >install.log 2>&1
