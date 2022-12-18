#!/bin/bash

cd "$(dirname "$0")" || exit

cat <<EOF | tee /home/$(whoami)/.local/share/altlinux/AltLinux.desktop >/dev/null
[Desktop Entry]
Name=AltLinux
GenericName=AltServer for Linux
Path=/usr/lib/altlinux
Exec=/usr/lib/altlinux/altlinux
Terminal=false
Type=Application
X-GNOME-Autostart-enabled=true
EOF

cp /home/$(whoami)/.local/share/altlinux/AltLinux.desktop /home/$(whoami)/.config/autostart/
rm /home/$(whoami)/.local/share/altlinux/AltLinux.desktop
