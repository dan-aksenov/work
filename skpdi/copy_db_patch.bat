REM copy patche to database patch subfolders.
REM parameter %1 to copy demo of prod(skpdi) patch
for /D %%a in ("d:\skpdi_patch\patches\*") do xcopy /y /d db_patch_%1..bat "%%a\"