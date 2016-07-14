IF NOT EXIST log MD log
IF NOT EXIST tmp MD tmp

set SRC_MIRROR=m:\SAA_DBRECOVERY_sbxaruee
set SRC_BACKUP=f:\SAA_DBRECOVERY_sbxaruee

set TMP_MIRROR=m:\MIRROR
set TMP_BACKUP=f:\BACKUP

IF NOT EXIST %TMP_MIRROR% MD %TMP_MIRROR%
IF NOT EXIST %TMP_BACKUP% MD %TMP_BACKUP%

echo 1 > tmp\arch.lock
xcopy %SRC_MIRROR% m:\MIRROR /s
xcopy %SRC_BACKUP% f:\BACKUP /s

rar a m:\curr.rar -m5 -df -r %TMP_MIRROR%
rar a f:\curr.rar -m5 -df -r %TMP_BACKUP%
del tmp\arch.lock

rd %TMP_MIRROR%
rd %TMP_BACKUP%

exit