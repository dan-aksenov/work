REM %1 - local of remote backup, %2 remote host, %3 network drive, %4 mapped drive

REM Perform day copy on midnight.
REM get current timestamp
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set curtime=%%a)
REM if timestamp starts with 00 initiate "daily backup"
if %curtime%==00 set TAG=day
REM if timestamp doesn't starts with 00 initiate "hourly(min) backup"
if not %curtime%==00 set TAG=min

REM Create logging folder and get timestamp for unique filenames
IF NOT EXIST log MD log
IF NOT EXIST tmp MD tmp
IF %TAG%==day set STAMP=%date:~-10,2%%date:~-7,2%%date:~-4,4%
IF %TAG%==min set STAMP=%time:~0,2%%time:~3,2%%time:~6,2%_%date:~-10,2%%date:~-7,2%%date:~-4,4%

REM Wait if another backup already in progress.
:wait
echo is another backup in progress?...
ping  127.0.0.1
IF EXIST tmp\copy.lock GOTO :wait

REM Create lock file to avoid interference from other backup jobs.
echo lock > tmp\copy.lock

REM mount remote network dirve, create backup directory and set propper attributes.
IF NOT EXIST %4:\ net use %4: \\%2\%3$ /USER:localhost\administrator Streaming911!
set DEST="%4:\REMOTE_BACKUP\%TAG%\%STAMP%"
IF NOT EXIST %DEST% MD %DEST%
attrib -A -H -S %DEST% /S

REM set directory names for local site
SET SRC_MIRROR=m:\SAA_DBRECOVERY_sbxaruee
SET SRC_BACKUP=f:\SAA_DBRECOVERY_sbxaruee
SET STAGE_MIRROR=m:\MIRROR_%1
SET STAGE_BACKUP=f:\BACKUP_%1

REM clear and recreate backup staging area
IF EXIST %STAGE_MIRROR% rd %STAGE_MIRROR% /q /s
IF EXIST %STAGE_BACKUP% rd %STAGE_BACKUP% /q /s
IF NOT EXIST %STAGE_MIRROR% MD %STAGE_MIRROR%
IF NOT EXIST %STAGE_BACKUP% MD %STAGE_BACKUP%
IF EXIST %STAGE_MIRROR%.RAR del %STAGE_MIRROR%.RAR /q
IF EXIST %STAGE_BACKUP%.RAR del %STAGE_BACKUP%.RAR /q

REM Start backup.
for /f %%i in ('time /t') do set START_TIME=%%i
@echo Backup started at %START_TIME%

REM Copy online backups to staging area
xcopy %SRC_MIRROR% %STAGE_MIRROR% /s
xcopy %SRC_BACKUP% %STAGE_BACKUP% /s
	
REM Archive backups in staging area
rar a %STAGE_MIRROR%.RAR -m5 -df -r %STAGE_MIRROR%  
rar a %STAGE_BACKUP%.RAR -m5 -df -r %STAGE_BACKUP%%  

time /t	
REM copy archives to remote backup destination
:copy1
xcopy %STAGE_MIRROR%.RAR %DEST% /z || goto :copy1
:copy2
xcopy %STAGE_BACKUP%.RAR %DEST% /z || goto :copy2
time /t

for /f %%i in ('time /t') do set END_TIME=%%i
@echo Backup completed at %END_TIME%

REM Remove old backups
REM set retention according to day or min backup.
if %tag%==day set retention=adddays(-2)
if %tag%==min set retention=addhours(-12)
REM forfiles -p %4:\REMOTE_BACKUP\%TAG% -s -m *.* %retention% /C "cmd /c del @path"

echo deleted because of retention settings
powershell -Command "Get-ChildItem %4:\REMOTE_BACKUP\%TAG% | where {$_.Lastwritetime -lt (date).%retention%}"
powershell -Command "Get-ChildItem %4:\REMOTE_BACKUP\%TAG% | where {$_.Lastwritetime -lt (date).%retention%} | remove-item -recurse -force -confirm:$false"
REM remove empty directories
for /f "delims=" %%d in ('dir %4:\REMOTE_BACKUP /s /b /ad ^| sort /r') do rd "%%d"

rem unmount network drive
rem net use %4: /delete
rem delete lock file
del tmp\copy.lock

REM append backup result to summary logfile
echo %STAMP% >> log\summary_%1.log
@findstr /c:"Backup started" "log\backup%1.log" >> log\summary_%1.log
@findstr /c:"File(s) copied" "log\backup%1.log" >> log\summary_%1.log
@findstr /c:"Backup completed" "log\backup%1.log" >> log\summary_%1.log
echo ############################################################################## >> log\summary_%1.log

rem exit