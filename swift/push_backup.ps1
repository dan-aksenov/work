# %1 - local of remote backup, %2 remote host, %3 network drive, %4 mapped drive
# Variables
$lock="tmp\copy.lock"

#create logging folder
IF NOT EXIST log MD log
IF NOT EXIST tmp MD tmp

# if day backup not exists make one
$tag="day"
$tag="min"

# get timestamp for unique dirnames
if ($tag -eq "day"){$stamp=$tag + $(get-date -f ddMMyyyy)}
if ($tag -eq "min"){$stamp=$tag + $(get-date -f HmddMMyyyy)}

# wait if another backup already in porgress 
while (Test-Path $lock) { Start-Sleep 10 }

echo lock > $lock
REM mount remote network dirve, create backup directory and set propper attributes
New-PSDrive –Name "$drive" –PSProvider FileSystem –Root "\\$host\$drive" –Persist
#IF NOT EXIST %4:\ net use %4: \\%2\%3$ /USER:host\user password
$dest=$drive + ":" + 
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

time /t	
REM copy archives to remote backup destination
:copy1
xcopy %STAGE_MIRROR%.RAR %DEST% /z || goto :copy1
:copy2
xcopy %STAGE_BACKUP%.RAR %DEST% /z || goto :copy2
time /t

# old files removal
# todo: add day/min differese
$limit = (Get-Date).AddDays(-15)
$path = "C:\Some\Path"
# Delete files older than the $limit.
Get-ChildItem -Path $path -Recurse -Force | Where-Object { !$_.PSIsContainer -and $_.CreationTime -lt $limit } | Remove-Item -Force
# Delete any empty directories left behind after deleting the old files.
Get-ChildItem -Path $path -Recurse -Force | Where-Object { $_.PSIsContainer -and (Get-ChildItem -Path $_.FullName -Recurse rem-Force | Where-Object { !$_.PSIsContainer }) -eq $null } | Remove-Item -Force -Recurse

#delete lock file
del $lock

exit