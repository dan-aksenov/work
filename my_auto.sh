ssh dstaksenov@10.73.7.11
pg_data=$(psql --no-align --tuples-only --command='show data_directory;')

sudo systemctl stop stolon-sentinel
sudo systemctl stop stolon-keeper
sudo systemctl stop stolon-proxy

sudo rm -r $pg_data/*
#sudo cp *.gz /var/lib/postgresql/sp03_kc_db01/postgres
#sudo cd /var/lib/postgresql/sp03_kc_db01/postgres

sudo tar -xvf /tmp/base.tar.gz --directory=$pg_data
sudo tar -xvf /tmp/pg_wal.tar.gz --directory=$pg_data/pg_wal

sudo systemctl start stolon-sentinel
sudo systemctl start stolon-keeper
sudo systemctl start stolon-proxy
systemctl status stolon-*