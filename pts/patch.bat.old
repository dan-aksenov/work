rem Update pts script.
set stage_dir=d:\pts_patch
set ssh_key=C:\Users\daniil.aksenov\Documents\ssh\id_rsa.ppk
set dst_host=%1
set usr_nix=ansible
rem %2 is positional parameter to add suffix if needed. Like apache-tomcat-8.5.4-dev. Dash needed!
set app_name=apache-tomcat-8.5.4%2
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%

rem Rename war files to desired names.
cd /d %stage_dir%
ren pts-integration-*.war integration.war
ren pts-public-*.war portal.war;
ren pts-restricted-*.war pts.war
ren pts-portal*.war portal2.war
ren pts-jointstorage*.war jointstorage.war

rem Stop tomcat.
%plink_cmd% "sudo systemctl stop tomcat%2"

rem Remove old app files and dirs
%plink_cmd% "sudo rm /opt/%app_name%/webapps/integration.war -f"
%plink_cmd% "sudo rm /opt/%app_name%/webapps/portal.war -f"
%plink_cmd% "sudo rm /opt/%app_name%/webapps/pts.war -f"
%plink_cmd% "sudo rm /opt/%app_name%/webapps/portal2.war"
%plink_cmd% "sudo rm /opt/%app_name%/webapps/jointstorage.war"

%plink_cmd% "sudo rm /opt/%app_name%/webapps/integration -rf"
%plink_cmd% "sudo rm /opt/%app_name%/webapps/portal -rf"
%plink_cmd% "sudo rm /opt/%app_name%/webapps/pts -rf"
%plink_cmd% "sudo rm /opt/%app_name%/webapps/portal2 -rf"
%plink_cmd% "sudo rm /opt/%app_name%/webapps/jointstorage -rf"

rem Copy files to nix machine.
%plink_cmd% "rm -rf /tmp/webapps && mkdir /tmp/webapps"
pscp -i %ssh_key% *.war %usr_nix%@%dst_host%:/tmp/webapps
%plink_cmd% "sudo chown tomcat.tomcat /tmp/webapps/*.war"
%plink_cmd% "sudo mv /tmp/webapps/*.war /opt/%app_name%/webapps" 

rem Check files md5.
md5sum integration.war
%plink_cmd% "sudo md5sum /opt/%app_name%/webapps/integration.war"
md5sum portal.war
%plink_cmd% "sudo md5sum /opt/%app_name%/webapps/portal.war"
md5sum pts.war
%plink_cmd% "sudo md5sum /opt/%app_name%/webapps/pts.war"
md5sum portal2.war
%plink_cmd% "sudo md5sum /opt/%app_name%/webapps/portal2.war"

rem Start tomcat.
%plink_cmd% "sudo systemctl start tomcat%2"

rem Check tomcat after starting.
%plink_cmd% "sudo systemctl status tomcat%2"