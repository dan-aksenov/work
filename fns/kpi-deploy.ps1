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
Catch {  BREAK  }

try {
Copy-Item -Path kpi-ta\Build\Debug\Build -Destination K:\Builds\Build$Stamp –Recurse
}
Catch {  BREAK  }

#copy deploy scripts
try {
Copy-Item -Path kpi-ta\Source\TRC\Source\Ais3.TRC.Resources\Scripts\trc-deploy.ps1 -Destination "K:\Builds\" -Force
Copy-Item -Path kpi-ta\Source\TRC\Source\Ais3.TRC.Resources\Scripts\trc-graceful-teardown-local.ps1 -Destination "K:\Builds\" -Force
Copy-Item -Path kpi-ta\Source\TRC\Source\Ais3.TRC.Resources\Scripts\trc-azman.psm1 -Destination "K:\Builds\" -Force
}
Catch {  BREAK  }

#run deployment scripts

try {
Invoke-command –computername 192.168.118.7 -credential $Cred –scriptblock { D:\Builds\trc-graceful-teardown-local.ps1 }
}
Catch {  BREAK  }

try {
Remove-Item -Recurse -Force K:\AIS3
Copy-Item -Path kpi-ta\Build\Debug\Build -Destination K:\AIS3 –Recurse -Force
}
Catch {  BREAK  }

try {
Invoke-command –computername 192.168.118.7 -credential $Cred -argumentlist $Stamp –scriptblock { 
Set-Location -Path "D:\Builds"
D:\Builds\trc-deploy.ps1 d:\AIS3 }
}
Catch {  BREAK  }

#compress build
try {
Invoke-command –computername 192.168.118.7 -credential $Cred -argumentlist $Stamp –scriptblock {
$src = "d:\Builds\Build$args"
$dst = "d:\Builds\Build$args.zip"
Add-Type -assembly "system.io.compression.filesystem"
[io.compression.zipfile]::CreateFromDirectory($src, $dst)
}
}
Catch {  BREAK  }

#delete folder
try {
Remove-Item K:\Builds\Build$Stamp -Force -Recurse
}
Catch {  BREAK  }

# Remove net drive
try {
Remove-PSDrive -Name "K"
}
Catch {  BREAK  }