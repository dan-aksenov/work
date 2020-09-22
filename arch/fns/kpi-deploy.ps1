[Console]::OutputEncoding = [Text.Encoding]::GetEncoding(1251)
$Username = 'localhost\Administrator'
$Password = 'Welcome4'
$pass = ConvertTo-SecureString -AsPlainText $Password -Force
$Cred = New-Object System.Management.Automation.PSCredential -ArgumentList $Username,$pass
$DeployHost = "192.168.118.7"
$Stamp = $(get-date -f yyyyMMdd_hh_mm_ss)

#Set-Item wsman:\localhost\Client\TrustedHosts -Value $DeployHost

# Add net drive
# check if exists
New-PSDrive –Name "K" –PSProvider FileSystem –Root "\\$DeployHost\D$" -Credential $Cred
if ($? -ne $true)
{
	write-host $?
	exit 1
}

Copy-Item -Path kpi-ta\Build\Debug\Build -Destination K:\Builds\Build$Stamp –Recurse
if ($? -ne $true)
{
	write-host $?
	exit 1
}

#copy deploy scripts
Copy-Item -Path kpi-ta\Source\TRC\Source\Ais3.TRC.Resources\Scripts\* -Destination "K:\Builds\" -Force
if ($? -ne $true)
{
	write-host $?
	exit 1
}

#run deployment scripts
Invoke-command –computername 192.168.118.7 -credential $Cred –scriptblock { D:\Builds\trc-graceful-teardown-local.ps1 }
if ($? -ne $true)
{
	write-host $?
	exit 1
}

Remove-Item -Recurse -Force K:\AIS3
if ($? -ne $true)
{
	write-host $?
	exit 1
}

Copy-Item -Path kpi-ta\Build\Debug\Build -Destination K:\AIS3 –Recurse -Force
if ($? -ne $true)
{
	write-host $?
	exit 1
}

Invoke-command –computername 192.168.118.7 -credential $Cred -argumentlist $Stamp –scriptblock { 
Set-Location -Path "D:\Builds"
D:\Builds\trc-deploy.ps1 d:\AIS3 }
if ($? -ne $true)
{
	write-host $?
	exit 1
}
else {
write-host Результат сборки: $?}

#compress build
Invoke-command –computername 192.168.118.7 -credential $Cred -argumentlist $Stamp –scriptblock {
$src = "d:\Builds\Build$args"
$dst = "d:\Builds\Build$args.zip"
Add-Type -assembly "system.io.compression.filesystem"
[io.compression.zipfile]::CreateFromDirectory($src, $dst)
}
if ($? -ne $true)
{
	write-host $?
	exit 1
}

#delete folder
Remove-Item K:\Builds\Build$Stamp -Force -Recurse
if ($? -ne $true)
{
	write-host $?
	exit 1
}

# Remove net drive
Remove-PSDrive -Name "K"
if ($? -ne $true)
{
	write-host $?
	exit 1
}