#!/bin/bash

cd "$(dirname "$0")" || exit

cat <<EOF | tee /home/$(whoami)/.local/share/althea/althea.desktop >/dev/null
[Desktop Entry]
Name=althea
GenericName=AltServer for Linux
Path=/usr/lib/althea
Exec=/usr/lib/althea/althea
Terminal=false
Type=Application
X-GNOME-Autostart-enabled=true
EOF

cp /home/$(whoami)/.local/share/althea/althea.desktop /home/$(whoami)/.config/autostart/
rm /home/$(whoami)/.local/share/althea/althea.desktop
