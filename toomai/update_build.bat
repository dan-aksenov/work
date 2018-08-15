@ECHO OFF

set ssh_key=C:\Users\daniil.aksenov\Documents\ssh\id_rsa.ppk
set usr_nix=ansible

set dst_host=toomai-pg
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%

echo Updateing %dst_host%

%plink_cmd% "sudo systemctl stop toomai-agent"
%plink_cmd% "sudo systemctl stop toomai"

psql -c "DROP SCHEMA toomai CASCADE" -U postgres -p 5432 -h toomai-pg postgres

pscp -i %ssh_key% \\SUNNY\Work\toomai\server\var\toomai\toomai-server.jar %usr_nix%@%dst_host%:/tmp/toomai-server.jar
%plink_cmd% "sudo cp /tmp/toomai-server.jar /var/toomai/toomai-server.jar"

pscp -i %ssh_key% \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar %usr_nix%@%dst_host%:/tmp/toomai-agent.jar
%plink_cmd% "sudo cp /tmp/toomai-agent.jar /var/toomai/toomai-agent.jar"

%plink_cmd% "sudo systemctl start toomai"
%plink_cmd% "sudo systemctl start toomai-agent"

echo Check md5 for %dst_host%
md5sum \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar
%plink_cmd% "sudo md5sum /var/toomai/toomai-agent.jar"
md5sum \\SUNNY\Work\toomai\server\var\toomai\toomai-server.jar
%plink_cmd% "sudo md5sum /var/toomai/toomai-server.jar"

set dst_host=toomai-oracle
set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%

echo Updateing %dst_host%
%plink_cmd% "sudo systemctl stop toomai-agent"
pscp -i %ssh_key% \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar %usr_nix%@%dst_host%:/tmp/toomai-agent.jar
%plink_cmd% "sudo cp /tmp/toomai-agent.jar /var/toomai/toomai-agent.jar"

%plink_cmd% "sudo systemctl start toomai-agent"

echo Check md5 for %dst_host%
md5sum \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar
%plink_cmd% "sudo md5sum /var/toomai/toomai-agent.jar"

rem set dst_host=toomai-deb
rem set plink_cmd=plink -i %ssh_key% %usr_nix%@%dst_host%
rem echo Updateing %dst_host%
rem %plink_cmd% "sudo systemctl stop toomai-agent"
rem pscp -i %ssh_key% \\SUNNY\Work\toomai\agent\var\toomai\toomai-agent.jar %usr_nix%@%dst_host%:/tmp/toomai-agent.jar
rem %plink_cmd% "sudo cp /tmp/toomai-agent.jar /var/toomai/toomai-agent.jar"
rem %plink_cmd% "sudo systemctl start toomai-agent"
rem md5sum \\SUNNY\Work\toomai\server\var\toomai\toomai-server.jar
rem %plink_cmd% "sudo md5sum /var/toomai/toomai-server.jar"
