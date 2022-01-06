$ErrorActionPreference = 'Stop'

# swig
$swigexe = Get-Command swig -ErrorAction "ignore"
if ($null -eq $swigexe) {
  & choco install swig --version 4.0.1 -y
  if (-not $?) { Write-Error -Message "swig installation failed" }
  $swig = Get-Command swig
}
Write-Output "SWIG found at:", $swig.Source

# openblas
New-Item -Path $env:OPENBLASROOT -ItemType "directory" -ErrorAction "ignore"
$openblaslib = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "openblas.lib" -ErrorAction "ignore"
$cblash = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "cblas.h" -ErrorAction "ignore"
$lapackeh = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "lapacke.h" -ErrorAction "ignore"

if (($null -eq $openblaslib) -or ($null -eq $cblash) -or ($null -eq $lapackeh)) {
  Invoke-WebRequest -Uri "https://anaconda.org/conda-forge/openblas/0.2.20/download/win-64/openblas-0.2.20-vc14_8.tar.bz2" -OutFile "openblas.tar.bz2"
  & 7z x openblas.tar.bz2
  & 7z x openblas.tar
  if (-not $?) { Write-Error "Unable to extract openblas" }
  Copy-Item -Path ".\Library\*" -Destination $env:OPENBLASROOT -Recurse
  # check that they all exist
  $openblaslib = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "openblas.lib"
  $cblash = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "cblas.h"
  $lapackeh = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "lapacke.h"
}

Write-Output "openblas.lib found at:", $openblaslib.Source, "cblas.h found at:", $cblash.Source, "lapacke.h found at", $lapackeh.Source

& python -m pip install -r recipe/cibw_before_requirements.txt
if (-not $?) { Write-Error -Message "requirements install failed" }
