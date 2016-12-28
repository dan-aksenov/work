#%1 - local of remote backup, %2 remote host, %3 network drive, %4 mapped drive

$SRC_MIRROR=m:\SAA_DBRECOVERY_sbxaruee
$SRC_BACKUP=f:\SAA_DBRECOVERY_sbxaruee
$STAGE_MIRROR=m:\MIRROR_%1
$STAGE_BACKUP=f:\BACKUP_%1
$LOG=

function f_robocopy  ($src, $dst, $tag) 
{ 
   robocopy $src $dst *.* /ndl /njh /njs /log:$LOG\copy_$tag.log
   #get file list ready for archiving
   (Get-Content $LOG\copy_$tag.log) | %{ $_.Split('c:')[2];} | %{ $_.Substring(32);} | Set-Content $LOG\diff_$tag.lst
   #archive diff
   type $LOG\diff_$tag.lst | zip $STAGE_MIRROR.zip -@
}

function 
{ 
   dir C:Windows | 
   where {$_.length –gt 100000} 
}

#IF %TAG%==day set STAMP=%date:~-10,2%%date:~-7,2%%date:~-4,4%
#IF %TAG%==min set STAMP=%time:~0,2%%time:~3,2%%time:~6,2%_%date:~-10,2%%date:~-7,2%%date:~-4,4%

#IF NOT EXIST log MD log
#IF NOT EXIST tmp MD tmp

#:wait
#echo is another backup in progress?...
#@ping  127.0.0.1
#IF EXIST tmp\copy_%1.lock GOTO :wait

echo lock > tmp\copy_$1.lock

IF NOT EXIST $STAGE_MIRROR MD $STAGE_MIRROR
IF NOT EXIST $STAGE_BACKUP MD $STAGE_BACKUP

#copy from source to stage make file list - redo as function
robocopy $SRC_MIRROR $STAGE_MIRROR *.* /ndl /njh /njs /log:log\copy_M.log
robocopy $SRC_BACKUP $STAGE_BACKUP *.* /ndl /njh /njs /log:log\copy_B.log

#get file list ready for archiving
(Get-Content .\copy.log) | %{ $_.Split('c:')[2];} | %{ $_.Substring(32);}

#zip or rar
cd $STAGE_MIRROR
type incr.lst | zip $STAGE_MIRROR.zip -@

cd $STAGE_BACKUP
type incr.lst | zip $STAGE_BACKUP.zip -@

time /t	
# copy archives to remote backup destination
:copy1
xcopy $STAGE_MIRROR.RAR $DEST /z || goto :copy1
:copy2
xcopy $STAGE_BACKUP.RAR $DEST /z || goto :copy2
time /t

#delete lock file
del tmp\copy_$1.lock /y