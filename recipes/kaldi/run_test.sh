#! /usr/bin/env bash

pkg-config --exists kaldi-base || exit 1
pkg-config --exists kaldi-matrix || exit 1
pkg-config --exists kaldi-thread || exit 1
pkg-config --exists kaldi-util || exit 1

CFLAGS=$(pkg-config --cflags kaldi-base kaldi-matrix kaldi-thread kaldi-util)
LDLIBS=$(pkg-config --libs kaldi-base kaldi-matrix kaldi-thread kaldi-util| xargs -n1 | sort -u | tr '\n' ' ')

cat > main.cpp <<- EOF
#include <iostream>
#include "matrix/matrix-common.h"
#include "util/kaldi-holder.h"

int main() {
  kaldi::Vector<float> vector(10, kaldi::kSetZero);
  vector.SetZero();
  kaldi::BasicHolder<float>::Write(std::cout, false, 0.0);
  return 0;
}
EOF

g++ main.cpp ${CFLAGS} \
  -lkaldi-base -lkaldi-thread -lkaldi-util -lkaldi-matrix -o yo ${LDLIBS} \
  || exit 1
./yo || exit 1