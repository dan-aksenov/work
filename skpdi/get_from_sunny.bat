REM create sunny path. %1 is patch number.
set sunny_path="\\sunny\builds\odsxp\%1\*.war"
xcopy %sunny_path% d:\skpdi_patch\
md5sum %sunny_path%
md5sum d:\skpdi_patch\