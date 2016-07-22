REM %1 - backup tag (day/min), %2 remote host, %3 network drive, %4 mapped drive

REM General setup
IF NOT EXIST log MD log
set TAG=%1
IF %TAG%==day set STAMP=%date:~-10,2%%date:~-7,2%%date:~-4,4%
IF %TAG%==min set STAMP=%time:~0,2%%time:~3,2%%time:~6,2%_%date:~-10,2%%date:~-7,2%%date:~-4,4%

REM Remote site 
net use %4: /delete

IF NOT EXIST %4:\ net use %4: \\%2\%3$ /USER:host\user password

set DEST="%4:\REMOTE_BACKUP\%TAG%_%STAMP%"
IF NOT EXIST %DEST% MD %DEST%
IF NOT EXIST %DEST%\MIRROR MD %DEST%\MIRROR
IF NOT EXIST %DEST%\BACKUP MD %DEST%\BACKUP

REM Local site 
SET SRC_MIRROR=m:\SAA_DBRECOVERY_sbxaruee
SET SRC_BACKUP=f:\SAA_DBRECOVERY_sbxaruee
SET STAGE_MIRROR=m:\MIRROR
SET STAGE_BACKUP=f:\BACKUP

REM clear staging area
IF EXIST %STAGE_MIRROR% rd %STAGE_MIRROR% /q /s
IF EXIST %STAGE_BACKUP% rd %STAGE_BACKUP% /q /s
IF NOT EXIST %STAGE_MIRROR% MD %STAGE_MIRROR%
IF NOT EXIST %STAGE_BACKUP% MD %STAGE_BACKUP%
IF EXIST %STAGE_MIRROR%.RAR del %STAGE_MIRROR%.RAR /q
IF EXIST %STAGE_BACKUP%.RAR del %STAGE_BACKUP%.RAR /q

REM Copy backups to staging area
xcopy %SRC_MIRROR% %STAGE_MIRROR% /s
xcopy %SRC_BACKUP% %STAGE_BACKUP% /s
	
REM Archive
rar a %STAGE_MIRROR%.RAR -m5 -df -r %STAGE_MIRROR%  
rar a %STAGE_BACKUP%.RAR -m5 -df -r %STAGE_BACKUP%%  
	
REM Copy staging to remote site
robocopy M:\ %DEST% *.RAR /LOG+:"log\%STAMP%.log" /NP /z
robocopy F:\ %DEST% *.RAR /LOG+:"log\%STAMP%.log" /NP /z 

rem robocopy %STAGE_MIRROR% %DEST%\MIRROR /LOG+:"log\%STAMP%.log" /NP /MIR /z 
rem robocopy %STAGE_BACKUP% %DEST%\BACKUP /LOG+:"log\%STAMP%.log" /NP /MIR /z 

REM Backup summary
findstr /r "Dirs Files Bytes Ended Times" "log\%STAMP%.log" | find /v "*.*" >> log\summary_%TAG%.log
echo ############################################################################## >> log\summary_%TAG%.log

REM Remove older files

exit
REM Remove older files
forfiles -p "%4\REMOTE_BACKUP" -s -m *.* /D -2 /C "cmd /c del @path"

net use %4: /delete
exit