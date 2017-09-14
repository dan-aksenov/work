REM create sunny path. %1 is patch number.
set sunny_path="\\sunny\builds\odsxp\%1\*.war"
rm 
xcopy %sunny_path% d:\skpdi_patch\
