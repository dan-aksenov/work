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
try {
New-PSDrive –Name "K" –PSProvider FileSystem –Root "\\$DeployHost\D$" -Credential $Cred
}
Catch { exit $LastExitCode }

try {
Copy-Item -Path kpi-ta\Build\Debug\Build -Destination K:\Builds\Build$Stamp –Recurse
}
Catch { exit $LastExitCode }

#copy deploy scripts
try {
Copy-Item -Path kpi-ta\Source\TRC\Source\Ais3.TRC.Resources\Scripts\trc-deploy.ps1 -Destination "K:\Builds\" -Force
}
Catch { exit $LastExitCode }

try {
Copy-Item -Path kpi-ta\Source\TRC\Source\Ais3.TRC.Resources\Scripts\trc-graceful-teardown-local.ps1 -Destination "K:\Builds\" -Force
}
Catch { exit $LastExitCode }
#run deployment scripts

try {
Invoke-command –computername 192.168.118.7 -credential $Cred –scriptblock { "D:\Builds\trc-graceful-teardown-local.ps1" }
}
Catch { exit $LastExitCode }

try {
Copy-Item -Path kpi-ta\Build\Debug\Build -Destination K:\AIS3 –Recurse -Force
}
Catch { exit $LastExitCode }


try {
Invoke-command –computername 192.168.118.7 -credential $Cred -argumentlist $Stamp –scriptblock { "D:\Builds\trc-deploy.ps1 d:\Builds\Build$args" }
}
Catch { exit $LastExitCode }

#compress build
try {
Invoke-command –computername 192.168.118.7 -credential $Cred -argumentlist $Stamp –scriptblock {
$src = "d:\Builds\Build$args"
$dst = "d:\Builds\Build$args.zip"
Add-Type -assembly "system.io.compression.filesystem"
[io.compression.zipfile]::CreateFromDirectory($src, $dst)
}
}
Catch { exit $LastExitCode }

#delete folder
try {
Remove-Item K:\Builds\Build$Stamp -Force -Recurse
}
Catch { exit $LastExitCode }

# Remove net drive
try {
Remove-PSDrive -Name "K"
}
Catch { exit $LastExitCode }