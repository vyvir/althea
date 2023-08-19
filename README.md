# ⚠️UNMAINTAINED/DEPRECATED⚠️ 
Currently, we are undergoing the process of privately testing and preparing a V2 release of AltLinux, the current public version (V1) has been deprecated, and is no longer guaranteed to work. We apologize for the inconvenience.
### FAQ
> When will AltLinux V2 be released?

Our team is currently facing some challenges with respect to the release date of V2. Recently, one of our core members became inactive, while we only have one active developer capable of working on the project right now. As a result, the timeline for its launch remains uncertain.
> V1 isn't working, how can I get support?

We no longer provide support for this version of AltLinux. If you need to sideload apps, we recommend using the official AltStore repo for the timebeing, using windows.
> I would like updates/I have a question about AltLinux

Please join [the Discord server](https://discord.gg/DZwRbyXq5Z) and we will be happy to answer any inquiries you may have.
# AltLinux
<img src="https://github.com/i-love-altlinux/AltLinux/blob/main/resources/4.png" alt="AltLinux Logo">

AltLinux is a GUI for AltServer-Linux that allows to easily sideload apps onto an iPhone, an iPad, or an iPod Touch. It supports iOS 12.2 and later.

Features:
- A straightforward GUI
- A tray menu that works just like on Windows
- Sideloading AltStore
- Sideloading apps without AltStore
- While the tray icon is present, AltServer runs in the background in tethered mode
- Launching the tray icon on start-up

The program is in its very early state, so if you're experiencing issues or want to help, you can join [the Discord server](https://discord.gg/DZwRbyXq5Z).

## Install AltLinux
⚠️ (Note: This version of AltLinux is deprecated, we cannot guarentee these instructions will work as intended) ⚠️

AltLinux is available for Ubuntu 22.04 and Ubuntu 20.04.

Derivatives, such as Linux Mint and Pop!_ OS should also work. To make sure which DEB package to pick, run the following command:

```
python3 --version
```

| Python 3.10          | Python 3.8        |
|:--------------------:|:-----------------:|
| Ubuntu 22.04         | Ubuntu 20.04      |
| Pop!_OS 22.04        | Pop!_OS 20.04     |
| Linux Mint 21        | Linux Mint 20     |
| elementary OS 7      | elementary OS 6   |
| Zorin OS 17          | Zorin OS 16       |

If you're running Ubuntu 22.04 or any distro based on it (such as Mint 21), install the DEB package [from here](https://github.com/i-love-altlinux/AltLinux/releases).

If you're running Ubuntu 20.04 or any distro based on it (such as Mint 20), run the following commands:
```
sudo add-apt-repository ppa:apandada1/libhandy-1
sudo apt update
sudo apt install libhandy-1-0 libhandy-1-dev
```

Then you can install the DEB package [from here](https://github.com/i-love-altlinux/AltLinux/releases).

If you use Arch Linux, you can use [the AUR package](https://aur.archlinux.org/packages/altlinux).

There is also a [git version](https://aur.archlinux.org/packages/altlinux-git) of AltLinux available as an AUR package.

If you use Fedora, you can [run the script without installing](#run-the-script-without-installing).

## Uninstall AltLinux

If you want to uninstall AltLinux, run the following commands:

```
sudo apt purge altlinux
```

```
sudo rm -rf /usr/lib/altlinux
```

```
rm -rf $HOME/.local/share/altlinux
```

## Run the script without installing

### Ubuntu:

Add the `universe` repository:

```
sudo add-apt-repository universe -y
```

Install the dependencies:
```
sudo apt-get install binutils python3-pip git gir1.2-appindicator3-0.1 usbmuxd libimobiledevice6 libimobiledevice-utils wget curl libavahi-compat-libdnssd-dev zlib1g-dev unzip usbutils
```

IF YOU'RE RUNNING UBUNTU 20.04 OR ITS [DERIVATIVES](https://github.com/i-love-altlinux/AltLinux#install-altlinux):
```
sudo add-apt-repository ppa:apandada1/libhandy-1
sudo apt update
sudo apt install libhandy-1-0 libhandy-1-dev
```

Run the following commands:
```
git clone https://github.com/i-love-altlinux/AltLinux
```

```
cd AltLinux
```

```
python3 main.py
```

### Fedora:

Install the dependencies:
```
sudo dnf install binutils python3-pip git libappindicator-gtk3 usbmuxd libimobiledevice-devel libimobiledevice-utils wget curl avahi-compat-libdns_sd-devel dnf-plugins-core unzip usbutils
```

Run the following commands:
```
git clone https://github.com/i-love-altlinux/AltLinux
```

```
cd AltLinux
```

```
python3 main.py
```

### Arch Linux

Install the dependencies:
```
sudo pacman -S binutils wget curl git python-pip libappindicator-gtk3 usbmuxd libimobiledevice avahi zlib unzip usbutils
```

Run the following commands:
```
git clone https://github.com/i-love-altlinux/AltLinux
```

```
cd AltLinux
```

```
python3 main.py
```

## Compile the DEB package
Add the `universe` repository:

```
sudo add-apt-repository universe -y
```

Install the dependencies:
```
sudo apt-get install binutils python3-pip git gir1.2-appindicator3-0.1 usbmuxd libimobiledevice6 libimobiledevice-utils wget curl libavahi-compat-libdnssd-dev zlib1g-dev unzip usbutils
```

If you're running Ubuntu 20.04 or any distro based on it (such as Mint 20), run the following commands:
```
sudo add-apt-repository ppa:apandada1/libhandy-1
sudo apt update
sudo apt install libhandy-1-0 libhandy-1-dev
```

Install pyinstaller:

```
pip3 install pyinstaller
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
AltServer-Linux made by [NyaMisty](https://github.com/NyaMisty)

Artwork by [Nebula](https://github.com/itsnebulalol)

Provision by [Dadoum](https://github.com/Dadoum)
