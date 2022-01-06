#! /usr/bin/env bash

set -e -x

if ! command -v swig; then
  HOMEBREW_NO_AUTO_UPDATE=1 brew install swig@4.0
fi
