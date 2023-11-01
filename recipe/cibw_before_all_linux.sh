#! /usr/bin/env bash

set -e -x

if command -v apk &> /dev/null; then
  # musllinux needs libexecinfo
  install_command="apk add"
  $install_command libexecinfo-dev || true
  export ADDITIONAL_LIBS=execinfo
fi