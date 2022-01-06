$ErrorActionPreference = 'Stop'
Set-PSDebug -Trace 1

# swig
$swigexe = Get-Command swig -ErrorAction "ignore"
if ($null -eq $swigexe) {
  & conda install swig=4.0.2 -y
  if (-not $?) { Write-Error -Message "swig installation failed" }
  $swig = Get-Command swig
}
Write-Output "SWIG found at:", $swig.Source

$openblaslib = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "openblas.lib" -ErrorAction "ignore"
$cblash = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "cblas.h" -ErrorAction "ignore"
$lapackeh = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "lapacke.h" -ErrorAction "ignore"

if (($null -eq $openblaslib) -or ($null -eq $cblash) -or ($null -eq $lapackeh)) {
  & conda create -n openblas-compile flang jom -c conda-forge -y
  if (-not $?) { Write-Error -Message "openblas environment creation failed" }
  & conda activate openblas-compile
  if (-not (Test-Path -Path "v0.3.19.zip")) {
    Invoke-WebRequest -Uri "https://github.com/xianyi/OpenBLAS/archive/v0.3.19.zip" -OutFile "v0.3.19.zip"
    if (-not ((Get-FileHash "v0.3.19.zip").Hash -eq "B3BECAEBC2CB905F4769EBEF621D7969002FF87BCBAA166C53338611E17AA05A")) {
      Write-Error -Message "Hash did not match"
    }
  }
  & 7z x "v0.3.19.zip"
  New-Item -Path ".\OpenBLAS-0.3.19\build" -ItemType "directory"
  Set-Location ".\OpenBLAS-0.3.19\build"
  & cmake .. -G "Nmake Makefiles JOM" "-DCMAKE_INSTALL_PREFIX=$env:OPENBLASROOT" -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER=clang-cl -DCMAKE_Fortran_COMPILER=flang -DCMAKE_MT=mt -DBUILD_WITHOUT_LAPACK=no -DNOFORTRAN=0 -DCMAKE_BUILD_TYPE=Release -DMSVC_STATIC_CRT=ON
  if (-not $?) { Write-Error -Message "cmake configuration failed" }
  & cmake --build . --target install
  if (-not $?) { Write-Error -Message "cmake build failed" }
  & conda deactivate
  if (-not $?) { Write-Error -Message "could not deactivate conda" }
  Pop-Location
  # check that they all exist
  $openblaslib = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "openblas.lib"
  $cblash = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "cblas.h"
  $lapackeh = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "lapacke.h"
}

Write-Output "openblas.lib found at:", $openblaslib.Source, "cblas.h found at:", $cblash.Source, "lapacke.h found at", $lapackeh.Source

& python -m pip install -r recipe/cibw_before_requirements.txt
if (-not $?) { Write-Error -Message "requirements install failed" }
