REM %1 - backup tag (day/min), %2 mapped network drive

REM General setup
IF NOT EXIST log MD log
set TAG=%1
IF %TAG%==day set STAMP=%date:~-10,2%%date:~-7,2%%date:~-4,4%
IF %TAG%==min set STAMP=%time:~0,2%%time:~3,2%%time:~6,2%_%date:~-10,2%%date:~-7,2%%date:~-4,4%

REM Remote site 
set DEST="%2\REMOTE_BACKUP\%TAG%_%STAMP%"
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

REM Copy backups to staging area
xcopy %SRC_MIRROR% %STAGE_MIRROR% /s
xcopy %SRC_BACKUP% %STAGE_BACKUP% /s

REM Copy staging to remote site
robocopy %STAGE_MIRROR% %DEST%\MIRROR /LOG+:"log\%STAMP%.log" /MIR /NJH /NFL /NP /NDL /MIR /MT /z 
robocopy %STAGE_BACKUP% %DEST%\BACKUP /LOG+:"log\%STAMP%.log" /MIR /NJH /NFL /NP /NDL /MIR /MT /z 

REM Backup summary
findstr /r "Dirs Files Bytes Ended Times" "log\%STAMP%.log" | find /v "*.*" >> log\summary_%TAG%.log
echo ############################################################################## >> log\summary_%TAG%.log

REM Remove older files

exit