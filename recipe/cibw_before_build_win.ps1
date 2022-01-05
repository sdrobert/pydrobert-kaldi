$ErrorActionPreference = 'Stop'
Set-PSDebug -Trace 1

choco install swig --version=4.0.1 -y

$tempFolderPath = Join-Path $Env:Temp $(New-Guid); New-Item -Type Directory -Path $tempFolderPath | Out-Null
Push-Location $tempFolderPath
Invoke-WebRequest -Uri "https://github.com/xianyi/OpenBLAS/archive/v0.3.19.zip" -OutFile "v0.3.19.zip"
if (-not ((Get-FileHash "v0.3.19.zip").Hash -eq "B3BECAEBC2CB905F4769EBEF621D7969002FF87BCBAA166C53338611E17AA05A")) {
  Write-Error -Message "Hash did not match"
}
7z x "v0.3.19.zip"
Set-Location ".\OpenBLAS-0.3.19"
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$env:OPENBLASROOT
cmake --build . --target install
Pop-Location

# nuget install OpenBLAS -Version 0.2.14.1 -OutputDirectory $env:OPENBLASROOT

Dir -Recurse $env:OPENBLASROOT

python -m pip install -r recipe/cibw_before_requirements.txt
