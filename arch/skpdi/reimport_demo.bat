set dbname=%1

set db_dest=-U postgres -p 5432 -h skpdi-test-db
set db_src=-U postgres -h gudhskpdi-db-01

reimport.bat