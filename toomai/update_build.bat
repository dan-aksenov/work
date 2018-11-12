@ECHO OFF

set ssh_key=C:\Users\%username%\Documents\ssh\id_rsa.ppk
set usr_nix=ansible

set dst_host=toomai-pg
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%

echo UPDATING %dst_host%
echo INITIAL CHECK MD5 FOR %dst_host%
md5sum \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar
%plink_cmd% "sudo md5sum /var/toomai/toomai-agent.jar"
md5sum \\SUNNY\Work\toomai\server\var\toomai\toomai-server.jar
%plink_cmd% "sudo md5sum /var/toomai/toomai-server.jar"

pause

%plink_cmd% "sudo systemctl stop toomai-agent"
%plink_cmd% "sudo systemctl stop toomai"

psql -c "DROP SCHEMA toomai CASCADE" -U postgres -p 5432 -h toomai-pg postgres

pscp -i %ssh_key% \\SUNNY\Work\toomai\server\var\toomai\toomai-server.jar %usr_nix%@%dst_host%:/tmp/toomai-server.jar
%plink_cmd% "sudo rm /var/toomai/toomai-server.jar"
%plink_cmd% "sudo cp /tmp/toomai-server.jar /var/toomai/toomai-server.jar"
%plink_cmd% "sudo chmod +x /var/toomai/toomai-server.jar"

pscp -i %ssh_key% \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar %usr_nix%@%dst_host%:/tmp/toomai-agent.jar
%plink_cmd% "sudo cp /tmp/toomai-agent.jar /var/toomai/toomai-agent.jar"

%plink_cmd% "sudo systemctl start toomai"
%plink_cmd% "sudo systemctl start toomai-agent"

echo FINAL CHECK MD5 FOR %dst_host%
md5sum \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar
%plink_cmd% "sudo md5sum /var/toomai/toomai-agent.jar"
md5sum \\SUNNY\Work\toomai\server\var\toomai\toomai-server.jar
%plink_cmd% "sudo md5sum /var/toomai/toomai-server.jar"

echo #
echo ########################################################################
echo #

set dst_host=toomai-oracle
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%

echo UPDATING %dst_host%
%plink_cmd% "sudo systemctl stop toomai-agent"
%plink_cmd% "sudo systemctl stop toomai-agent"

pscp -i %ssh_key% \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar %usr_nix%@%dst_host%:/tmp/toomai-agent.jar
%plink_cmd% "sudo cp /tmp/toomai-agent.jar /var/toomai/toomai-agent.jar"
%plink_cmd% "sudo systemctl start toomai-agent"

echo FINAL CHECK MD5 FOR %dst_host%
md5sum \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar
%plink_cmd% "sudo md5sum /var/toomai/toomai-agent.jar"

echo #
echo ########################################################################
echo #

set dst_host=toomai-deb
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%
echo UPDATEING %dst_host%
%plink_cmd% "sudo systemctl stop toomai-agent"
pscp -i %ssh_key% \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar %usr_nix%@%dst_host%:/tmp/toomai-agent.jar
%plink_cmd% "sudo cp /tmp/toomai-agent.jar /var/toomai/toomai-agent.jar"
%plink_cmd% "sudo systemctl start toomai-agent"
echo FINAL CHECK MD5 FOR %dst_host%
md5sum \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar
%plink_cmd% "sudo md5sum /var/toomai/toomai-agent.jar"

echo #
echo ########################################################################
echo #

exit
REM powershell section disabled so far...

set dst_host=toomai-mssql
powershell -Command "Start-Process sc '\\%toomai-mssql% stop toomai-agent' -Verb RunAs"
del /f "\\%dst_host%\c$\Program Files\toomai\toomai-agent.jar"
del /f "\\%dst_host%\c$\Program Files\toomai\toomai-agent.exe"
copy "\\sunny\Work\toomai\windows\toomai-agent.jar" "\\%dst_host%\c$\Program Files\toomai\"
copy "\\sunny\Work\toomai\windows\toomai-agent.exe" "\\%dst_host%\c$\Program Files\toomai\"
powershell -Command "Start-Process sc '\\%toomai-mssql% start toomai-agent' -Verb RunAs"

set dst_host=kite
powershell -Command "Start-Process sc '\\%toomai-mssql% stop toomai-agent' -Verb RunAs"
del /f "\\%dst_host%\c$\Program Files\toomai\toomai-agent.jar"
del /f "\\%dst_host%\c$\Program Files\toomai\toomai-agent.exe"
copy "\\sunny\Work\toomai\windows\toomai-agent.jar" "\\%dst_host%\c$\Program Files\toomai\"
copy "\\sunny\Work\toomai\windows\toomai-agent.exe" "\\%dst_host%\c$\Program Files\toomai\"
powershell -Command "Start-Process sc '\\%toomai-mssql% start toomai-agent' -Verb RunAs"


