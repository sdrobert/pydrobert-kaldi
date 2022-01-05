$ErrorActionPreference = 'Stop'
Set-PSDebug -Trace 1

choco install swig --version=4.0.1 -y

$libpath = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "openblas.lib" -ErrorAction "ignore"
$cblaspath = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "cblas.h" -ErrorAction "ignore"
$lapackepath = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "lapacke.h" -ErrorAction "ignore"

if (($null -eq $libpath) -or ($null -eq $cblaspath) -or ($null -eq $lapackepath)) {
  $tempFolderPath = Join-Path $Env:Temp $(New-Guid); New-Item -Type Directory -Path $tempFolderPath | Out-Null
  Push-Location $tempFolderPath
  Invoke-WebRequest -Uri "https://github.com/xianyi/OpenBLAS/archive/v0.3.19.zip" -OutFile "v0.3.19.zip"
  if (-not ((Get-FileHash "v0.3.19.zip").Hash -eq "B3BECAEBC2CB905F4769EBEF621D7969002FF87BCBAA166C53338611E17AA05A")) {
    Write-Error -Message "Hash did not match"
  }
  7z x "v0.3.19.zip"
  Set-Location ".\OpenBLAS-0.3.19"
  & cmake -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_INSTALL_PREFIX=$env:OPENBLASROOT"
  Get-Content -Path "CMake*"
  Write-Error -Message "Crap"
  if (-not $?) { Write-Error -Message "cmake configuration failed" }
  & cmake --build . --target install
  if (-not $?) { Write-Error -Message "cmake build failed" }
  Pop-Location
  # check that they all exist
  Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "openblas.lib"
  Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "cblas.h"
  Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "lapacke.h"
}

Get-ChildItem -Recurse $env:OPENBLASROOT

python -m pip install -r recipe/cibw_before_requirements.txt
