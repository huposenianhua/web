#!/bin/bash
set -e

mkdir -p /var/www/html/woody/res/debug
chown -R www-data:www-data /var/www/html

sed -i 's/FILTER_FLAG_IPV4 | FILTER_FLAG_NO_PRIV_RANGE/FILTER_FLAG_IPV4/' /var/www/html/woody/php/url.php || true

php -r "
\$conn = mysqli_connect('mysql', 'n5gl0n39mnyn183l_woody', '.@=6207zmt');
mysqli_query(\$conn, 'CREATE DATABASE IF NOT EXISTS n5gl0n39mnyn183l_camman DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci');
mysqli_query(\$conn, 'INSERT IGNORE INTO n5gl0n39mnyn183l_camman.gb2312 SELECT * FROM palmmicro.gb2312');
" 2>/dev/null || true

service cron start || cron

exec "$@"
