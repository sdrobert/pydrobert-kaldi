#! /usr/bin/env bash

set -e -x

if command -v apk &> /dev/null; then
  install_command="apk add"
  $install_command libexecinfo-dev || true
fi