REM create sunny path. %1 is patch number.
set sunny_path="\\sunny\builds\odsxp\%1"
del /q d:\skpdi_patch\
xcopy /e %sunny_path% d:\skpdi_patch\
