REM create sunny path. %1 is patch number.
set sunny_path="\\sunny\builds\odsxp\%1"
REM Clear and recreate stage directory.
rmdir /s /q d:\skpdi_patch
md d:\skpdi_patch
xcopy /e %sunny_path% d:\skpdi_patch\
