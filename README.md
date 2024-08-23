# althea
<img src="https://github.com/vyvir/althea/blob/main/resources/4.png" alt="althea Logo">

althea is a GUI for AltServer-Linux that allows to easily sideload apps onto an iPhone, an iPad, or an iPod Touch. It supports iOS 15 and later. althea supports x86_64, aarch64, and armv7.

This app is in a very early state, so if you're experiencing issues or want to help, you can create a [pull request](https://github.com/vyvir/althea/pulls), [report an issue](https://github.com/vyvir/althea/issues), or join [the Discord server](https://discord.gg/DZwRbyXq5Z).

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

### Running althea

Once the dependencies are installed, run the following commands:
```
git clone https://github.com/vyvir/althea
```

```
cd althea
```

```
python3 main.py
```

Note: if you're running OpenSUSE Leap, run the following command instead:
```
python3.11 main.py
```

That's it! Have fun with althea!

## Credits

althea made by [vyvir](https://github.com/vyvir)

AltServer-Linux made by [NyaMisty](https://github.com/NyaMisty)

Provision by [Dadoum](https://github.com/Dadoum)

Artwork by [Nebula](https://github.com/itsnebulalol)
