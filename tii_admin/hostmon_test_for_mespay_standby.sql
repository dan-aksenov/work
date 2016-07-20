set ver off head off
whenever sqlerror exit :rc

-- Presuming standby mounted only

-- Connect to standby site
conn sys/pass@proton as sysdba

-- Get current scn
var scn number;
begin
select current_scn into :scn from v$database;
end;
/

col scn format 99999999999999999999999999
print :scn

-- Connect to primary site
conn user/pass@mespaydb

var rc number;

col lag_sec new_value err_count

-- Compare scns
select extract( day from diff )*24*60*60 + extract( hour from diff )*60*60 + extract( minute from diff )*60 + round(extract( second from diff)) lag_sec from ( select scn_to_timestamp((select current_scn from v$database))-scn_to_timestamp((select :scn from v$database)) diff from dual);

exec :rc:=&err_count;
/

-- If lag threshold exeeded send alert to Hostmon.
begin if 
	:rc < 600
	then :rc:=-1;
	end if;
end;
/

exit :rc
