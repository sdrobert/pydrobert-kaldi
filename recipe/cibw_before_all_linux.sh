#! /usr/bin/env bash

set -e -x

if command -v apk &> /dev/null; then
  # musllinux doesn't have execinfo
  export NO_EXECINFO=1
fi