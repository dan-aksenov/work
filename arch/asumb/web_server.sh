yum install gcc openssl-devel libmemcached-devel supervisor git memcached
nginx

rpm -Uvh https://mirror.webtatic.com/yum/el7/webtatic-release.rpm
yum install php70w-fpm php70w-mbstring php70w-pgsql php70w-zip php70w-ѕxml php70w-gd php70w-pear php70w-devel php70w-mcrypt

git clone https://github.com/php-memcached-dev/php-memcached
cd php-memcached
git checkout -b php7 origin/php7
./configure
./make
make
make install

echo extension=memcached.so >/etc/php.d/memcached.ini

systemctl restart php-fpm
systemctl enable php-fpm

mkdir /data/www/sump

#Копируем исходный код СУМП в директорию проекта
cp /source/ /data/www/sump

cat > /etc/nginx/default.d/sump.conf <<EOF
server {
proxy_max_temp_file_size 0;
listen 80;
sendfile on;
tcp_nopush on;
tcp_nodelay on;
keepalive_timeout 65;
root /data/www/sump/public;
access_log /var/log/nginx/nginx_access.log;
error_log /var/log/nginx/nginx_error.log;
location / {
try_files $uri $uri/ /index.php$is_args$args;
}location /status {
stub_status;
}
location /fpmstatus {
access_log off;
allow 127.0.0.1;
allow all;
includefastcgi_params;
fastcgi_indexindex.php;
fastcgi_param SCRIPT_FILENAME
$document_root$fastcgi_script_name;
fastcgi_pass 127.0.0.1:9000;
}
client_max_body_size 256m;
index index.html index.php;
location ~ \.php$ {
fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
fastcgi_pass 127.0.0.1:9000;
fastcgi_indexindex.php;
fastcgi_split_path_info^(.+\.php)(.*)$;
includefastcgi_params;
fastcgi_buffers 32 32k;
fastcgi_buffer_size 32k;
try_files $uri =404;
}
location ~ /\. {
deny all;
}
location ~* \.(css|gif|ico|jpeg|jpg|js|svg|png)$ {
expires 1h;
}
}
EOF

#or www.conf?
cat > /etc/php-fpm.d/sump.conf <<EOF
[www]
user = www-data
group = www-data
listen = 127.0.0.1:9000
listen.owner = www-data
pm = ondemand
pm.max_children = 300
pm.start_servers = 32
pm.min_spare_servers = 2
pm.max_spare_servers = 4
pm.max_requests = 1024
pm.status_path = /fpmstatus
listen.backlog = -1
php_admin_value[short_open_tag] = 1
php_admin_value[memory_limit] = 1024M
request_terminate_timeout = 300s
php_value[max_execution_time] = 120
php_value[post_max_size] = 256M
php_value[upload_max_filesize] = 256M
pm.status_path = /fpm-status
php_admin_value[error_log] = /data/www/logs/fpm-php.www.log
php_admin_flag[log_errors] = on
catch_workers_output = yes
EOF

systemctl restart php-fpm nginx

cd /data/www/sump
# php composer
php composer.phar update

chown -R www-data:www-data /data/www/sump

cat > ./config/sump.php <<EOF
<?php
return [
'modules' => [
'Tables',
'Api',
'Integration',
'Dictionaries',
'Users',
'Core',
'OrganizationalUnits',
'Works',
'Reports',
],
'version' => '01.01.30.21',
'audit' =>env('AUDIT_ACTIVE', true),// телефон технической поддержки
'support_phone' => '+7 (000) 000-00-00',
// аккаунт для отправки sms
'devinotele' => [
// логин
'login' => '',
// пароль
'password' => '',
// адрес отправителя
'source' => '',
],
// карты
'map' => [
// типкарты: osm, yandex
'type' => 'yandex',
// OSM Карты (host - url ГЕО-сервера системы)
'osm' => [
'host' => '',
'path' => '/tiles',
'port' => '80',
'name' => 'Картография',
],
],
// Маршрутизатор (host - url ГЕО-сервера системы)
'graphhopper' => [
'host' => ''
'path' => '/graphhopper/route',
'port' => '80',
'name' => 'Маршруты',
],
]
EOF

cat >/modules/Integration/config/integration.php <<EOF
<?php
// URL шлюза интеграции
return [
'url' => 'http://172.16.2.185/osb_mes_test/ru.tii.ku_api.ps',
'login' => 'asumb',
'password' => 'xxxx',
// максимальное количество назначенных работ при автоматическом
распределении
'assigned_max_count' => 10,
'employers_start_date' => '01.01.2017',
];
EOF


cat >..\modules\Api\Service\V1\SessionService.php <<EOF
protected function getUpdateInfo()
{
return [
'appName' => 'sump',
'appDescription' => 'СУМП',
'packageName' => 'com.softwarecenter',
'versionCode' => '8',
'versionName' => '1.0',
'forceUpdate' => false,
'autoUpdate' => false,
'apkUrl' => 'http://URL/assets/mobile_update/sump.apk',
'updateTips' => 'СУМП ПМv1.0',
];
}
EOF