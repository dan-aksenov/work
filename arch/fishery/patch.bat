rem Update pts script.
set stage_dir=d:\fishery_patch
set ssh_key=C:\Users\daniil.aksenov\Documents\ssh\id_rsa.ppk
set dst_host=%1
set usr_nix=ansible
rem %2 is positional parameter to add suffix if needed. Like apache-tomcat-8.5.4-dev. Dash needed!
set app_name=apache-tomcat-8.5.8%2
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%

rem Rename war files to desired names.
cd /d %stage_dir%
ren fishery-integration-*.war integration.war
ren fishery-public-*.war portal.war;
ren fishery-restricted-*.war fishery.war

rem Stop tomcat.
%plink_cmd% "sudo systemctl stop tomcat%2"

rem Remove old app files and dirs
%plink_cmd% "sudo rm /u01/%app_name%/webapps/integration.war -f"
%plink_cmd% "sudo rm /u01/%app_name%/webapps/portal.war -f"
%plink_cmd% "sudo rm /u01/%app_name%/webapps/fishery.war -f"

%plink_cmd% "sudo rm /u01/%app_name%/webapps/integration -rf"
%plink_cmd% "sudo rm /u01/%app_name%/webapps/portal -rf"
%plink_cmd% "sudo rm /u01/%app_name%/webapps/fishery -rf"

rem Copy files to nix machine.
%plink_cmd% "rm -rf /tmp/webapps && mkdir /tmp/webapps"
pscp -i %ssh_key% *.war %usr_nix%@%dst_host%:/tmp/webapps
%plink_cmd% "sudo chown tomcat.tomcat /tmp/webapps/*.war"
%plink_cmd% "sudo mv /tmp/webapps/*.war /u01/%app_name%/webapps" 

rem Check files md5.
md5sum integration.war
%plink_cmd% "sudo md5sum /u01/%app_name%/webapps/integration.war"
md5sum portal.war
%plink_cmd% "sudo md5sum /u01/%app_name%/webapps/portal.war"
md5sum fishery.war
%plink_cmd% "sudo md5sum /u01/%app_name%/webapps/fishery.war"

rem Start tomcat.
%plink_cmd% "sudo systemctl start tomcat%2"

rem Check tomcat after starting.
%plink_cmd% "sudo systemctl status tomcat%2"