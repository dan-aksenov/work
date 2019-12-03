#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "1 for patch number" 
    exit 1
fi

ver=$1

ssh ansible@ats-rd sudo pkill java
ssh ansible@ats-rd sudo rm /u01/apache-tomcat-8.5.8/webapps/ats-rd* -rf

sudo mount -t drvfs '\\sunny\builds\ats\' /mnt/sunny
rsync -avz /mnt/sunny/$ver /tmp/stage
cd /tmp/stage/$ver/patch
psql -h ats-rd -p 5432 -U postgres ats-test<install.sql &/tmp/install_$ver.log

tail /tmp/install_$ver.log
read -p "Press [Enter] key to proceed..."

ssh ansible@ats-rd mkdir /tmp/stage
scp /tmp/stage/$ver/ats-rd-server-$ver.war ansible@ats-rd:/tmp/stage
ssh ansible@ats-rd sudo cp /tmp/stage/ats-rd-server-$ver.war /u01/apache-tomcat-8.5.8/webapps/ats-rd.war
ssh ansible@ats-rd sudo chown tomcat.tomcat /u01/apache-tomcat-8.5.8/webapps/ats-rd.war

md5sum /mnt/sunny/$ver/ats-rd-server-$ver.war
ssh ansible@ats-rd sudo md5sum /u01/apache-tomcat-8.5.8/webapps/ats-rd.war
read -p "Press [Enter] key to proceed..."
ssh ansible@ats-rd sudo -u tomcat /u01/apache-tomcat-8.5.8/bin/startup.sh

cd -
rm -rf /tmp/stage
sudo umount /mnt/sunny
