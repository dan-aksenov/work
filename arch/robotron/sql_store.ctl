-- Please review these options to fit your needs
OPTIONS (skip=1, direct=true, silent=(feedback) )
-- The specified characterset might not be correct, please check the Oracle documentation
LOAD DATA CHARACTERSET 'AL32UTF8'
INFILE 'sql_store.dat'
-- to replace the data in the table use TRUNCATE instead of APPEND
TRUNCATE
INTO TABLE SQL_STORE
FIELDS TERMINATED BY '|' TRAILING NULLCOLS
(
  NM_QUERY,
  DT_LOAD,
  lob_file_SQL_QUERY FILLER,
  SQL_QUERY LOBFILE(lob_file_SQL_QUERY) TERMINATED BY EOF
)