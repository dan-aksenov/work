IF NOT EXIST log MD log
set log=%date:~-10,2%%date:~-7,2%%date:~-4,4%.log

set tag=day
set src=192.168.12.1

set SRC_MIRROR=\\%SRC%\m$\SAA_DBRECOVERY_sbxaruee
set SRC_BACKUP=\\%SRC%\f$\SAA_DBRECOVERY_sbxaruee

set DST_MIRROR=E:\MIRROR\%tag%
set DST_BACKUP=E:\BACKUP\%tag%

IF NOT EXIST %DST_MIRROR% MD %DST_MIRROR%
IF NOT EXIST %DST_BACKUP% MD %DST_BACKUP%

REM MOVE "current" to "previous"
del %DST_MIRROR%\prev\prev.rar /y
rar a %DST_MIRROR%\prev\prev.rar -m5 -df -r %DST_MIRROR%\curr

rem backup "source" to "current"
robocopy %SRC_MIRROR% %DST_MIRROR%\curr /LOG+:"log\%log%" /NJH /NFL /NP /NDL /MIR /MT /z 

rem copy "current" to "previous"
del %DST_BACKUP%\prev\prev.rar /y
rar a %DST_BACKUP%\prev\prev.rar -m5 -df -r %DST_BACKUP%\curr

rem backup "source" to "current"
robocopy %SRC_BACKUP% %DST_BACKUP%\curr /LOG+:"log\%log%" /NJH /NFL /NP /NDL /MIR /MT /z 

rem summary
findstr /r "Dirs Files Bytes Ended" log\%log% | find /v "*.*" >> log\summary_%tag%.log
echo ############################################################################## >> log\summary_%tag%.log

rem purge older logs
forfiles -p ".\log" -s -m *.* /D -1 /C "cmd /c del @path"

exit