DBNAME=$1
ROLENAME=$2

#1. create database
psql -h localhost -U postgres <<EOF
CREATE DATABASE $DBNAME OWNER $ROLENAME
EOF

#2. load extentions
psql -h localhost -U postgres <<EOF
create trusted language pltcl;
create trusted language pltclu;
UPDATE pg_language set lanpltrusted = true where lanname='pltclu';
CREATE EXTENSION adminpack SCHEMA pg_catalog;
CREATE EXTENSION dblink SCHEMA public;
CREATE EXTENSION pg_stat_statements SCHEMA public;
CREATE EXTENSION pldbgapi SCHEMA public;
CREATE EXTENSION plpythonu SCHEMA pg_catalog;
CREATE EXTENSION pg_buffercache SCHEMA public;
EOF

#3' todo exp/imp only metadata, exp/imp needed spr tables

#3. import etalon (add logging)
pg_restore --host localhost --port 5432 --username postgres --dbname $DBNAME --role $ROLENAME --no-password  --no-owner --no-privileges --no-tablespaces --verbose .\etalon.dmp
