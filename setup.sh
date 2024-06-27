#!/bin/bash

REP_BASE=`pwd`
echo "Repertoire de base : ${REP_BASE}"

echo "Installer environnement de developpement ARM"
sudo apt update
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi build-essential

echo "Compiler mpy-cross tool "
cd "${REP_BASE}/micropython/"
make -C mpy-cross
make -C ports/rp2 BOARD=PICO_W submodules

#echo "Installer environnement de developpement thonny"
#sudo apt install thonny
