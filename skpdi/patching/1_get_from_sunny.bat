REM create sunny path. %1 is patch number.
set sunny_path="\\sunny\builds\odsxp\%1"
REM Clear and recreate stage directory.
del d:\skpdi_patch\* /S /Q

xcopy /e %sunny_path% d:\skpdi_patch\
