REM %1 - local of remote backup, %2 remote host, %3 network drive, %4 mapped drive

REM perform day copy on midnight
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set curtime=%%a)
if %curtime%==0 set TAG=day
if not %curtime%==0 set TAG=min

REM create logging folder and get timestamp for unique filenames
IF NOT EXIST log MD log
IF %TAG%==day set STAMP=%date:~-10,2%%date:~-7,2%%date:~-4,4%
IF %TAG%==min set STAMP=%time:~0,2%%time:~3,2%%time:~6,2%_%date:~-10,2%%date:~-7,2%%date:~-4,4%

REM mount remote network dirve, create backup directory and set propper attributes
IF NOT EXIST %4:\ net use %4: \\%2\%3$ /USER:host\user password
set DEST="%4:\REMOTE_BACKUP\%TAG%_%STAMP%"
IF NOT EXIST %DEST% MD %DEST%
attrib -A -H -S %DEST% /S

REM set directory names for local site
SET SRC_MIRROR=m:\SAA_DBRECOVERY_sbxaruee
SET SRC_BACKUP=f:\SAA_DBRECOVERY_sbxaruee
SET STAGE_MIRROR=m:\MIRROR_%1
SET STAGE_BACKUP=f:\BACKUP_%1

REM clear and recreate staging area
IF EXIST %STAGE_MIRROR% rd %STAGE_MIRROR% /q /s
IF EXIST %STAGE_BACKUP% rd %STAGE_BACKUP% /q /s
IF NOT EXIST %STAGE_MIRROR% MD %STAGE_MIRROR%
IF NOT EXIST %STAGE_BACKUP% MD %STAGE_BACKUP%
IF EXIST %STAGE_MIRROR%.RAR del %STAGE_MIRROR%.RAR /q
IF EXIST %STAGE_BACKUP%.RAR del %STAGE_BACKUP%.RAR /q

REM Copy online backups to staging area
xcopy %SRC_MIRROR% %STAGE_MIRROR% /s
xcopy %SRC_BACKUP% %STAGE_BACKUP% /s
	
REM Archive backups in staging area
rar a %STAGE_MIRROR%.RAR -m5 -df -r %STAGE_MIRROR%  
rar a %STAGE_BACKUP%.RAR -m5 -df -r %STAGE_BACKUP%%  
	
REM copy archives to remote backup destination
:copy1
xcopy %STAGE_MIRROR%.RAR %DEST% /z || goto :copy1
:copy2
xcopy %STAGE_BACKUP%.RAR %DEST% /z || goto :copy2



REM append current backup's result to summary logfile
findstr /r "Dirs Files Bytes Ended Times" "log\%STAMP%.log" | find /v "*.*" >> log\summary_%TAG%.log
echo ############################################################################## >> log\summary_%TAG%.log

REM remove old backups 
forfiles -p "%4\REMOTE_BACKUP\day*" -s -m *.* /D -2 /C "cmd /c del @path"
forfiles -p "%4\REMOTE_BACKUP\min*" -s -m *.* /D -1 /C "cmd /c del @path"

rem unmount network drive
net use %4: /delete
exit