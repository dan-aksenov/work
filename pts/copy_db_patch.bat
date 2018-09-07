REM copy patch executor to database patch subfolders.
REM parameter %1 to copy master or branch patch
for /D %%a in ("d:\pts_patch\*") do xcopy /y /d .\%1\db-%1.bat "%%a\patches\"
for /D %%a in ("d:\pts_patch\*") do xcopy /y /d .\%1\db-trans-%1.bat "%%a\jointstorage_patches\"

for /D %%a in ("d:\pts_patch\*") do xcopy /y /d .\%1\db-BEL-%1.bat "%%a\patches\"