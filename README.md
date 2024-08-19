# AltLinux
<img src="https://github.com/i-love-altlinux/AltLinux/blob/main/resources/4.png" alt="AltLinux Logo">

AltLinux is a GUI for AltServer-Linux that allows to easily sideload apps onto an iPhone, an iPad, or an iPod Touch. It supports iOS 15 and later. AltLinux supports x86_64, aarch64, and armv7.

This app is in a very early state, so if you're experiencing issues or want to help, you can create a [pull request](https://github.com/i-love-altlinux/AltLinux/pulls), [report an issue](https://github.com/i-love-altlinux/AltLinux/issues), or join [the Discord server](https://discord.gg/DZwRbyXq5Z).

## Instructions

### Dependencies

Ubuntu:
```
sudo apt install software-properties-common
```

```
sudo add-apt-repository universe -y
```

```
sudo apt-get install binutils python3-pip git gir1.2-appindicator3-0.1 usbmuxd libimobiledevice6 libimobiledevice-utils wget curl libavahi-compat-libdnssd-dev zlib1g-dev unzip usbutils libhandy-1-dev gir1.2-notify-0.7 python3-requests psmisc
```

Fedora:
```
sudo dnf install binutils python3-pip git libappindicator-gtk3 usbmuxd libimobiledevice-devel libimobiledevice-utils wget curl avahi-compat-libdns_sd-devel dnf-plugins-core unzip usbutils psmisc
```
Arch Linux:
```
sudo pacman -S binutils wget curl git python-pip python-gobject libappindicator-gtk3 usbmuxd libimobiledevice avahi zlib unzip usbutils psmisc libhandy
```

OpenSUSE:
```
sudo zypper in binutils wget curl git python311-gobject-Gdk libhandy-devel libappindicator3-1 typelib-1_0-AppIndicator3-0_1 imobiledevice-tools libdns_sd libnotify-devel psmisc
```

### Running AltLinux

Once the dependencies are installed, run the following commands:
```
git clone https://github.com/i-love-altlinux/AltLinux
```

```
cd AltLinux
```

```
python3 main.py
```

Note: if you're running OpenSUSE Leap, run the following command instead:
```
python3.11 main.py
```

## Compile the DEB package
**
This installation method is no longer supported.**
If you still wish to cotribute to it, feel free to create a [pull request](https://github.com/i-love-altlinux/AltLinux/pulls).

Add the `universe` repository:

```
sudo apt install software-properties-common
```

```
sudo add-apt-repository universe -y
```

Install the dependencies:
```
sudo apt-get install binutils python3-pip git gir1.2-appindicator3-0.1 usbmuxd libimobiledevice6 libimobiledevice-utils wget curl libavahi-compat-libdnssd-dev zlib1g-dev unzip usbutils libhandy-1-dev gir1.2-notify-0.7 python3-requests psmisc pipx
```

If you're running Ubuntu 20.04 or any distro based on it (such as Mint 20), run the following commands:
```
sudo add-apt-repository ppa:apandada1/libhandy-1
sudo apt update
sudo apt install libhandy-1-0 libhandy-1-dev
```

Install pyinstaller:

Ubuntu 22.04:
```
pip3 install pyinstaller
```

Ubuntu 24.04:
```
pip3 install pyinstaller --break-system-packages
```

Reboot your computer for changes to take effect.

After that, proceed by running the following commands:
```
git clone https://github.com/i-love-altlinux/AltLinux
```

```
cd AltLinux
```

```
./build.sh
```

The DEB file is ready! You can install it now.

## Credits

AltLinux made by [vyvir](https://github.com/vyvir)

AltServer-Linux made by [NyaMisty](https://github.com/NyaMisty)

Provision by [Dadoum](https://github.com/Dadoum)

Artwork by [Nebula](https://github.com/itsnebulalol)
