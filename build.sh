#!/bin/bash

REP_BASE=`pwd`
REP_ESP32="${REP_BASE}/micropython/ports/esp32"
REP_MG_SRC="${REP_BASE}/crypto_c_lib/src"

export USER_C_MODULES="${REP_MG_SRC}/micropython.cmake"

rm "${REP_BASE}/firmware.bin"

cd "$REP_ESP32"

if [ -z $NOCLEAN ]; then
  echo "Cleaning project by default"
  make clean
fi
make
cp "${REP_BASE}/micropython/ports/esp32/build-ESP32_GENERIC/firmware.bin" "${REP_BASE}"
