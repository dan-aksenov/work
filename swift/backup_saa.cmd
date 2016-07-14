REM RUN VARIABLE SECTION
rem set log=%date:~-10,2%%date:~-7,2%%date:~-4,4%.log
set log=%time:~0,2%%time:~3,2%%time:~6,2%_%date:~-10,2%%date:~-7,2%%date:~-4,4%.log

rem set tag=day
set tag=min

set src=192.168.12.1

set SRC_MIRROR=\\%SRC%\m$\
set SRC_BACKUP=\\%SRC%\f$\

set DST_MIRROR=C:\MIRROR\%tag%
set DST_BACKUP=C:\BACKUP\%tag%

IF NOT EXIST %DST_MIRROR% MD %DST_MIRROR%
IF NOT EXIST %DST_BACKUP% MD %DST_BACKUP%

if not exist \\%src%\C$\scripts\backup\tmp\arch.lock goto :resume
:wait
echo waiting for remote archival to complete...
@ping 127.0.0.1 -n 5
if exist \\%src%\C$\scripts\backup\tmp\arch.lock goto :wait

:resume
REM MOVE "current" to "previous"
move %DST_MIRROR%\curr.rar %DST_MIRROR%\prev.rar

rem backup "source" to "current"
robocopy %SRC_MIRROR% %DST_MIRROR% curr.rar /LOG+:"log\%log%" /NJH /NFL /NP /NDL /MT /z 

rem copy "current" to "previous"
move %DST_BACKPU%\curr.rar %DST_BACKUP%\prev.rar

rem backup "source" to "current"
robocopy %SRC_BACKUP% %DST_BACKUP% curr.rar /LOG+:"log\%log%" /NJH /NFL /NP /NDL /MT /z 

rem summary
findstr /r "Dirs Files Bytes Ended" "log\%log%" | find /v "*.*" >> log\summary_%tag%.log
echo ############################################################################## >> log\summary_%tag%.log

rem purge older logs
forfiles -p ".\log" -s -m *.* /D -120 /C "cmd /c del @path"

exit