# Развертывание стендов STAGE1 DEMO

ssh dstaksenov@10.72.4.9

sudo su postgres
cd /data/backups/huawei/postgres

scp -r             pg-security-1/basebackup/pg-security-1-2020-09-22 dstaksenov@10.73.7.11:/home/dstaksenov
scp -r pg-business-shard-1/basebackup/pg-business-shard-1-2020-09-22 dstaksenov@10.73.7.10:/home/dstaksenov
scp -r     pg-notification-1/basebackup/pg-notification-1-2020-09-22 dstaksenov@10.73.7.13:/home/dstaksenov
scp -r                   pg-group-1/basebackup/pg-group-1-2020-09-22 dstaksenov@10.73.7.18:/home/dstaksenov
scp -r                 pg-global-1/basebackup/pg-global-1-2020-09-22 dstaksenov@10.73.7.14:/home/dstaksenov
scp -r                   pg-gamif-1/basebackup/pg-gamif-1-2020-09-22 dstaksenov@10.73.7.17:/home/dstaksenov
scp -r               pg-content-1/basebackup/pg-content-1-2020-09-22 dstaksenov@10.73.7.12:/home/dstaksenov
scp -r   pg-configuration-1/basebackup/pg-configuration-1-2020-09-22 dstaksenov@10.73.7.19:/home/dstaksenov


psql --no-align --tuples-only --command='show data_directory;'

-- kc security
ssh dstaksenov@10.73.7.11
/var/lib/postgresql/sp03_kc_db01/postgres
-- shard
ssh dstaksenov@10.73.7.10
/var/lib/postgresql/sp03_shd1_db01/postgres

/var/lib/postgresql/sp03_notif_db01/postgres
/var/lib/postgresql/sp03_group_db01/postgres
/var/lib/postgresql/sp03_glob_db01/postgres
/var/lib/postgresql/sp03_gamif_db01/postgres
/var/lib/postgresql/sp03_cont_db01/postgres
/var/lib/postgresql/sp03_conf_db01/postgres


sudo su

systemctl stop stolon-sentinel
systemctl stop stolon-keeper
systemctl stop stolon-proxy

rm -r   /var/lib/postgresql/sp03_shd1_db01/postgres/*
cp *.gz /var/lib/postgresql/sp03_shd1_db01/postgres
cd      /var/lib/postgresql/sp03_shd1_db01/postgres

tar -xvf base.tar.gz
tar -xvf pg_wal.tar.gz --directory=pg_wal
rm *.gz

systemctl restart stolon-sentinel
systemctl restart stolon-keeper
systemctl restart stolon-proxy
systemctl status stolon-*

# в бд edupower
SELECT  'ALTER SERVER ' || srvname || ' OPTIONS (SET hostaddr ''10.73.7.1''); '
        || '-- ' || current_database()
FROM pg_foreign_server
ORDER BY srvname;

\gexec


-- audit
pg_dump --host=10.72.6.14 --port=5439 --username=postgres --dbname=edu_power_audit --exclude-table-data=edu_power_audit.audit_messages --exclude-table-data=edu_power_audit.z_audit_messages_old  --file=$(date '+%Y-%m-%d')_edu_power_audit-schema.sql --verbose


SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'edu_power_audit_old_old';
DROP DATABASE IF EXISTS edu_power_audit_old_old;

SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'edu_power_audit_old';
ALTER DATABASE edu_power_audit_old RENAME TO edu_power_audit_old_old;

SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'edu_power_audit';
ALTER DATABASE edu_power_audit RENAME TO edu_power_audit_old;

CREATE DATABASE edu_power_audit OWNER edu_power_audit;

\connect edu_power_audit

\i /home/dstaksenov/2020


--------------------------------------------------------------------------------
-- наливаем mongo

-- Целевая машина 
ssh dstaksenov@10.73.7.20

scp dstaksenov@10.72.4.9:/data/backups/huawei/mongodb/sp2-mng-db-01/2020-09-15/2020-09-15_10-00.dat .
scp dstaksenov@10.72.4.9:/data/backups/huawei/mongodb/sp2-mng-db-01/2020-09-21/2020-09-21_10-00.dat .


mongorestore --host 10.73.7.1 --port 27017 --authenticationDatabase admin --username edupower -d edupower --drop --archive=2020-09-15_10-00.dat


mongo --host 10.73.7.1 --port 27017 --authenticationDatabase admin --username mongo-admin

mongo --host 10.73.7.1 --port 27017 --authenticationDatabase admin --username edupower


