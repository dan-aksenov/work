src_host=$1
src_db=$2
dmp_dir=$3

echo Dump and download $src_db database.
time ssh $src_host sudo -u postgres pg_dump $src_db -Fc -Z5 --exclude-table-data "event.fdc_app_log_*" --exclude-table-data "parameter.fdc_parameter_md" -f $dmp_dir/reimp.dmp
time scp $src_host:$dmp_dir/reimp.dmp /tmp/
