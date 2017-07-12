set stage_dir=d:\pts_patch
set ssh_key=C:\Users\daniil.aksenov\Documents\ssh\id_rsa.ppk
set dst_nix=%1
set usr_nix=ansible
rem Positional parameter to add suffix if needed. Like apache-tomcat-8.5.4-dev. Dash needed!
set app_name=apache-tomcat-8.5.4%2

rem Rename war files to desired names.
cd /d %stage_dir%
ren pts-integration-*.war integration.war
ren pts-public-*.war portal.war;
ren pts-restricted-*.war pts.war

rem Stop tomcat.
plink -i %ssh_key% %usr_nix%@%dst_host% "sudo systemctl stop tomcat%2"

rem Remove old app files and dirs
plink -i %ssh_key% %usr_nix%@%dst_host% "sudo rm /opt/%app_name%/webapps/*.war
plink -i %ssh_key% %usr_nix%@%dst_host% "sudo rm /opt/%app_name%/webapps/integration -rf
plink -i %ssh_key% %usr_nix%@%dst_host% "sudo rm /opt/%app_name%/webapps/portal -rf
plink -i %ssh_key% %usr_nix%@%dst_host% "sudo rm /opt/%app_name%/webapps/pts -rf

rem Copy files to nix machine.
plink -i %ssh_key% %usr_nix%@%dst_host% "mkdir /tmp/webapps"
pscp -i %ssh_key% *.war %usr_nix%@%dst_host%:/tmp/webapps
plink -i %ssh_key% %usr_nix%@%dst_host% "sudo cp /tmp/webapps/*.war /opt/%app_name%/webapps 

rem Start tomcat.
plink -i %ssh_key% %usr_nix%@%dst_host% "sudo systemctl start tomcat%2"

