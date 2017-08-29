rem Update pts script.
set stage_dir=d:\skpdi_patch
set ssh_key=C:\Users\daniil.aksenov\Documents\ssh\id_rsa.ppk
set dst_host=%1
set usr_nix=ansible
set app_name=apache-tomcat-8.5.5
set app_path=/u01/%app_name%/webapps
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%

rem Rename war files to desired names.
cd /d %stage_dir%
ren *.war demo.war

rem Ensure tomcat stopped.
%plink_cmd% "sudo systemctl stop tomcat"

rem Remove old app files and dirs
%plink_cmd% "sudo rm %app_path%/*.war"
%plink_cmd% "sudo rm %app_path%/demo -rf"

rem Copy files to nix machine.
%plink_cmd% "rm -rf /tmp/webapps && mkdir /tmp/webapps"
pscp -i %ssh_key% *.war %usr_nix%@%dst_host%:/tmp/webapps
%plink_cmd% "sudo chown tomcat.tomcat /tmp/webapps/*.war"
%plink_cmd% "sudo mv /tmp/webapps/*.war %app_path%" 

rem Check files md5.
md5sum demo.war
%plink_cmd% "sudo md5sum %app_path%/demo.war"

rem Start tomcat.
%plink_cmd% "sudo systemctl start tomcat%2"

rem Check tomcat after starting.
%plink_cmd% "sudo systemctl status tomcat%2"
