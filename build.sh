#!/bin/bash

REP_BASE=`pwd`
REP_ESP32="${REP_BASE}/micropython/ports/esp32"
REP_MG_SRC="${REP_BASE}/crypto_c_lib/src"

export USER_C_MODULES="${REP_MG_SRC}/micropython.cmake"

rm "${REP_BASE}/firmware.bin"

mkdir -p "${REP_ESP32}/modules/"
cp -rf "${REP_BASE}/cyberfly_sdk/"* "${REP_ESP32}/modules/"

cd "$REP_ESP32"

if [ -z $NOCLEAN ]; then
  echo "Cleaning project by default"
  make clean
fi
make BOARD=ESP32_GENERIC
cp "${REP_BASE}/micropython/ports/esp32/build-ESP32_GENERIC/firmware.bin" "${REP_BASE}"
