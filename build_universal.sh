#!/bin/bash

cd "$(dirname "$0")" || exit

if [ -d "./althea/usr/lib" ]; then
    rm -rf "./AltServer/usr/lib"
fi
if [ -d "./dist" ]; then
    rm -rf "./dist"
fi

pyinstaller althea.spec --clean
cp -R ./resources ./dist/althea
mkdir -p "./althea/usr/lib"

cp -R ./dist/althea ./althea/usr/lib
chmod -R 0775 althea
