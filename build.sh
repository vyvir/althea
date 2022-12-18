#!/bin/bash

cd "$(dirname "$0")" || exit

if [ -d "./AltLinux/usr/lib" ]; then
    rm -rf "./AltServer/usr/lib"
fi
if [ -d "./dist" ]; then
    rm -rf "./dist"
fi

pyinstaller altlinux.spec --clean
cp -R ./resources ./dist/altlinux
mkdir -p "./AltLinux/usr/lib"

cp -R ./dist/altlinux ./AltLinux/usr/lib
chmod -R 0775 AltLinux
dpkg-deb --build --root-owner-group AltLinux AltLinux.deb
