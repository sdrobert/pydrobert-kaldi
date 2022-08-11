$ErrorActionPreference = 'Stop'

# swig
$swigexe = Get-Command swig -ErrorAction "ignore"
if ($null -eq $swigexe) {
  & choco install swig --version 4.0.1 -y
  if (-not $?) { Write-Error -Message "swig installation failed" }
  $swigexe = Get-Command swig
}

# openblas
if (-not ([string]::IsNullOrEmpty($env:OPENBLASROOT))) {
  New-Item -Path $env:OPENBLASROOT -ItemType "directory" -ErrorAction "ignore"
  $openblaslib = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "openblas.lib" -ErrorAction "ignore"
  $cblash = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "cblas.h" -ErrorAction "ignore"
  $lapackeh = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "lapacke.h" -ErrorAction "ignore"

  if (($null -eq $openblaslib) -or ($null -eq $cblash) -or ($null -eq $lapackeh)) {
    Invoke-WebRequest -Uri "https://anaconda.org/conda-forge/openblas/0.2.20/download/win-64/openblas-0.2.20-vc14_8.tar.bz2" -OutFile "openblas.tar.bz2"
    $hash = Get-FileHash openblas.tar.bz2
    if (-not ($hash.Hash -eq "74BB55BCC4C5B760A08424ED7A53D08FF9581278BB05441F7F6E5F43AADCF8CA")) { Write-Error "openblas hash does not match" }
    & 7z x openblas.tar.bz2
    & 7z x -aoa openblas.tar
    if (-not $?) { Write-Error "Unable to extract openblas" }
    Invoke-WebRequest -Uri "https://anaconda.org/conda-forge/libflang/5.0.0/download/win-64/libflang-5.0.0-vc14_1.tar.bz2" -OutFile "libflang.tar.bz2"
    $hash = Get-FileHash libflang.tar.bz2
    if (-not ($hash.Hash -eq "BC50A67898F82820F5138938FBAABC90CF13495CE188E91725A33B6FAD25F06F")) { Write-Error "libflang hash does not match" }
    & 7z x libflang.tar.bz2
    & 7z x -aoa libflang.tar
    if (-not $?) { Write-Error "Unable to extract libflang" }
    Copy-Item -Path ".\Library\*" -Destination $env:OPENBLASROOT -Recurse
    # check that they all exist
    $openblaslib = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "openblas.lib"
    $cblash = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "cblas.h"
    $lapackeh = Get-ChildItem -Path $env:OPENBLASROOT -Recurse -Filter "lapacke.h"
  }
}