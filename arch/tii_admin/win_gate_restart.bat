rem server_name(gate,gate1,gate2)
sc \\%1 stop WinGateEngine
sc \\%1 start WinGateEngine
pause