@ECHO OFF
REM Update skpdi application.
REM Staging local dir to hold application data to be pushed.
set stage_dir=d:\skpdi_patch
REM Users public key must be allowed in server's authorized_keys file.
set ssh_key=C:\Users\daniil.aksenov\Documents\ssh\id_rsa.ppk
set usr_nix=ansible
REM Host to be updated.
set dst_host=%1
REM Applicateion name skpdi or demo. Passed as second parameter.
set app_name=%2
REM Tomcat name to create path.
set tomcat_name=apache-tomcat-8.5.8
REM Create application folder for future use.
set app_path=/u01/%tomcat_name%/webapps
REM Create plink command for use in script below.
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%

REM Rename war files to desired names.
rem cd /d %stage_dir%
ren %stage_dir%\*.war %stage_dir%\%app_name%.war

REM Ensure tomcat stopped.
%plink_cmd% "sudo systemctl stop tomcat"

REM Remove old app files and dirs
%plink_cmd% "sudo rm %app_path%/%app_name%.war -f"
%plink_cmd% "sudo rm %app_path%/%app_name% -rf"

REM Copy files to nix machine.
%plink_cmd% "rm -rf /tmp/webapps && mkdir /tmp/webapps"
pscp -i %ssh_key% *.war %usr_nix%@%dst_host%:/tmp/webapps
%plink_cmd% "sudo chown tomcat.tomcat /tmp/webapps/*.war"
%plink_cmd% "sudo mv /tmp/webapps/*.war %app_path%" 

REM Check copied files md5. To be compared with source.
md5sum %app_name%.war
%plink_cmd% "sudo md5sum %app_path%/%app_name%.war"

REM Start tomcat.
rem Tomcat start commented out. Manual startap suggested.
rem %plink_cmd% "sudo systemctl start tomcat"
REM Check tomcat after starting.
rem %plink_cmd% "sudo systemctl status tomcat"