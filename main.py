#!/usr/bin/python
import os
import errno
from re import T
from shutil import rmtree
import json
import urllib.request
from urllib.request import urlopen
import urllib.parse
import requests
import subprocess
import signal
import threading
from time import sleep
import platform

# PyGObject

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Handy", "1")
gi.require_version("Notify", "0.7")
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import Gtk, AppIndicator3 as appindicator
except ValueError: # Fix for Solus and other Ayatana users
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import Gtk, AyatanaAppIndicator3 as appindicator
from gi.repository import GLib
from gi.repository import GObject, Handy
from gi.repository import GdkPixbuf
from gi.repository import Notify
from gi.repository import Gdk

GObject.type_ensure(Handy.ActionRow)

installedcheck = False
computer_cpu_platform = platform.machine()

def resource_path(relative_path):
    global installedcheck
    CheckRun10 = subprocess.run(
        f"find /usr/lib/althea/althea > /dev/null 2>&1", shell=True
    )
    if CheckRun10.returncode == 0:
        installedcheck = True
        base_path = "/usr/lib/althea"
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Global variables
ipa_path_exists = False  # Checks if the IPA path has been defined by user
savedcheck = False
InsAltStore = subprocess.Popen(
    "test", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
)
lolcheck = "lol"  # Redirects user either to login or to file chooser; If the "Pair" option was selected, it closes the dialog
apple_id = "lol"
password = "lol"
Warnmsg = "warn"
Failmsg = "fail"
icon_name = "changes-prevent-symbolic"
command_six = Gtk.CheckMenuItem(label="Launch at Login")
AltServer = "$HOME/.local/share/althea/AltServer"
AnisetteServer = "$HOME/.local/share/althea/anisette-server"
AltStore = "$HOME/.local/share/althea/AltStore.ipa"
PATH = AltStore
AutoStart = resource_path("resources/AutoStart.sh")
altheapath = os.path.join(
    os.environ.get("XDG_DATA_HOME") or f'{ os.environ["HOME"] }/.local/share',
    "althea",
)

# Check version
with open(resource_path("resources/version"), "r", encoding="utf-8") as f:
    LocalVersion = f.readline().strip()

# Functions
def connectioncheck():
    try:
        urlopen("http://www.example.com", timeout=5)
        return True
    except:
        return False

def menu():
    menu = Gtk.Menu()

    if (notify()) == True:
        command_upd = Gtk.MenuItem(label="Download Update")
        command_upd.connect("activate", showurl)
        menu.append(command_upd)

        menu.append(Gtk.SeparatorMenuItem())

    command_one = Gtk.MenuItem(label="About althea")
    command_one.connect("activate", on_abtdlg)
    menu.append(command_one)

    menu.append(Gtk.SeparatorMenuItem())

    command_two = Gtk.MenuItem(label="Install AltStore")
    command_two.connect("activate", altstoreinstall)
    menu.append(command_two)

    command_three = Gtk.MenuItem(label="Install an IPA file")
    command_three.connect("activate", altserverfile)
    menu.append(command_three)

    command_four = Gtk.MenuItem(label="Pair")
    command_four.connect("activate", lambda x: openwindow(PairWindow))
    menu.append(command_four)

    command_five = Gtk.MenuItem(label="Restart AltServer")
    command_five.connect("activate", restartaltserver)
    menu.append(command_five)

    menu.append(Gtk.SeparatorMenuItem())

    CheckRun11 = subprocess.run(f"test -e /usr/lib/althea/althea", shell=True)
    if CheckRun11.returncode == 0:
        global command_six
        CheckRun12 = subprocess.run(
            f"test -e $HOME/.config/autostart/althea.desktop", shell=True
        )
        if CheckRun12.returncode == 0:
            command_six.set_active(command_six)
        command_six.connect("activate", launchatlogin1)
        menu.append(command_six)

    exittray = Gtk.MenuItem(label="Quit althea")
    exittray.connect("activate", lambda x: quitit())
    menu.append(exittray)

    menu.show_all()
    return menu

def on_abtdlg(self):
    about = Gtk.AboutDialog()
    width = 100
    height = 100
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
        resource_path("resources/3.png"), width, height
    )
    about.set_logo(pixbuf)
    about.set_program_name("althea")
    about.set_version("0.5.0")
    about.set_authors(
        [
            "vyvir",
            "AltServer-Linux",
            "made by NyaMisty",
            "Provision",
            "made by Dadoum",
        ]
    )  # , 'Provision made by', 'Dadoum'])
    about.set_artists(["nebula"])
    about.set_comments("A GUI for AltServer-Linux written in Python.")
    about.set_website("https://github.com/vyvir/althea")
    about.set_website_label("Github")
    about.set_copyright("GUI by vyvir")
    about.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
    about.run()
    about.destroy()

def paircheck():  # Check if the device is paired already
    pairchecking = subprocess.run('idevicepair pair | grep -q "SUCCESS"', shell=True)
    if pairchecking.returncode == 0:
        return False
    else:
        return True

def altstoreinstall(_):
    if paircheck():
        global lolcheck
        lolcheck = "altstr"
        openwindow(PairWindow)
    else:
        win1()

def altserverfile(_):
    if paircheck():
        global lolcheck
        lolcheck = "ipa"
        openwindow(PairWindow)
    else:
        win2 = FileChooserWindow()
        global ipa_path_exists
        if ipa_path_exists == True:
            global PATH
            PATH = win2.PATHFILE
            win1()
            ipa_path_exists = False

def notify():
    if (connectioncheck()) == True:
        LatestVersion = (
            urllib.request.urlopen(
                "https://raw.githubusercontent.com/vyvir/althea/main/resources/version"
            )
            .readline()
            .rstrip()
            .decode()
        )
        if LatestVersion > LocalVersion:
            Notify.init("MyProgram")
            n = Notify.Notification.new(
                "An update is available!",
                "Click 'Download Update' in the tray menu.",
                resource_path("resources/3.png"),
            )
            n.set_timeout(Notify.EXPIRES_DEFAULT)
            # n.add_action("newupd", "Download", actionCallback)
            n.show()
            return True
        else:
            return False
    else:
        return False

def showurl(_):
    Gtk.show_uri_on_window(
        None, "https://github.com/vyvir/althea/releases", Gdk.CURRENT_TIME
    )
    quitit()

def openwindow(window):
    w = window()
    w.show_all()

def quitit():
    subprocess.run(f"killall {AltServer}", shell=True)
    subprocess.run(f"killall {AnisetteServer}", shell=True)
    Gtk.main_quit()
    os.kill(os.getpid(), signal.SIGKILL)

def restartaltserver(_):
    subprocess.run(f"killall {AltServer}", shell=True)
    subprocess.run(f"killall {AnisetteServer}", shell=True)
    subprocess.run("idevicepair pair", shell=True)
    subprocess.run(
        f"""export ALTSERVER_ANISETTE_SERVER='http://127.0.0.1:6969' ; {(altheapath)}/AltServer &""",
        shell=True,
    )

def winerm():
    silent_remove(f"{(altheapath)}/log.txt")
    dialog = Gtk.MessageDialog(
        # transient_for=self,
        flags=0,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text="Do you want to login automatically?",
    )
    dialog.format_secondary_text("Your login and password have been saved earlier.")
    response = dialog.run()
    if response == Gtk.ResponseType.YES:
        global apple_id
        global password
        try:
            with open(f"{(altheapath)}/saved.txt", "r") as f:
                for line in f:
                    if 'ł' in line:
                        apple_id, password = line.split("ł")
                        break
                    else:
                        print("Invalid line format:", line)
                        continue
            print(apple_id, password)
            global savedcheck
            savedcheck = True
            Login().on_click_me_clicked1()
        except ValueError as e:
            print("Error reading credentials:", e)
        except FileNotFoundError as e:
            print("File not found:", e)
    else:
        silent_remove(f"{(altheapath)}/saved.txt")
        win3 = Login()
        win3.show_all()
    dialog.destroy()

def win1():
    if os.path.isfile(f"{(altheapath)}/saved.txt"):
        winerm()
    else:
        openwindow(Login)

def win2(_):
    if os.path.isfile(f"{(altheapath)}/saved.txt"):
        winerm()
    else:
        openwindow(Login)

def actionCallback(notification, action, user_data=None):
    Gtk.show_uri_on_window(
        None, "https://github.com/vyvir/althea/releases", Gdk.CURRENT_TIME
    )
    quitit()

def launchatlogin1(_):
    global command_six
    if command_six.get_active():
        global AutoStart
        os.popen(AutoStart).read()
        return True
    else:
        silent_remove("$HOME/.config/autostart/althea.desktop")
        return False

def silent_remove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred

def altstore_download(value):
    # setting the base URL value
    baseUrl = "https://cdn.altstore.io/file/altstore/apps.json"

    # retrieving data from JSON Data
    json_data = requests.get(baseUrl)
    if json_data.status_code == 200:
        data = json_data.json()
        for app in data['apps']:
            if app['name'] == "AltStore":
                if value == "Check":
                    size = app['versions'][0]['size']
                    return size == os.path.getsize(f'{(altheapath)}/AltStore.ipa')
                    break
                if value == "Download":
                    latest = app['versions'][0]['downloadURL']
                    r = requests.get(
                        latest,
                        allow_redirects=True,
                    )
                    latest_filename = latest.split('/')[-1]
                    open(f"{(altheapath)}/{(latest_filename)}", "wb").write(r.content)
                    os.rename(f"{(altheapath)}/{(latest_filename)}", f"{(altheapath)}/AltStore.ipa")
                    subprocess.run(f"chmod 755 {(altheapath)}/AltStore.ipa", shell=True)
                    break
        return True
    else:
        return False

def ios_version():
    silent_remove(f"{(altheapath)}/ideviceinfo.txt")
    subprocess.run(f"ideviceinfo > {(altheapath)}/ideviceinfo.txt", shell=True)
    result = "result"
    pathsy = f"{(altheapath)}/ideviceinfo.txt"
    with open(pathsy) as file:
        # Iterate through lines
        for line in file.readlines():
            # Find the start of the word
            index = line.find("ProductVersion: ")
            # If the word is inside the line
            if index != -1:
                result = line[:-1][16:]
    silent_remove(f"{(altheapath)}/ideviceinfo.txt")
    print(result)
    return(result)

# Classes
class SplashScreen(Handy.Window):
    def __init__(self):
        super().__init__(title="Loading")
        self.set_resizable(False)
        self.set_default_size(512, 288)
        self.present()
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_keep_above(True)

        self.mainBox = Gtk.Box(
            spacing=6,
            orientation=Gtk.Orientation.VERTICAL,
            halign=Gtk.Align.START,
            valign=Gtk.Align.START,
        )
        self.add(self.mainBox)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join("resources/4.png"),
            width=512,
            height=288,
            preserve_aspect_ratio=False,
        )
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.show()
        self.mainBox.pack_start(image, False, True, 0)

        self.lbl1 = Gtk.Label(label="Starting althea...")
        self.mainBox.pack_start(self.lbl1, False, False, 6)
        self.loadalthea = Gtk.ProgressBar()
        self.mainBox.pack_start(self.loadalthea, True, True, 0)
        self.t = threading.Thread(target=self.startup_process)
        self.t.start()
        self.wait_for_t(self.t)

    def wait_for_t(self, t):
        if not self.t.is_alive():
            global indicator
            indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
            self.t.join()
            self.destroy()
        else:
            GLib.timeout_add(200, self.wait_for_t, self.t)

    def startup_process(self):
        self.lbl1.set_text("Checking if anisette-server is already running...")
        self.loadalthea.set_fraction(0.1)
        command = 'curl 127.0.0.1:6969 | grep -q "{"'
        CheckRun = subprocess.run(command, shell=True)
        if not os.path.isfile(f"{(altheapath)}/anisette-server"):
            self.lbl1.set_text("Downloading anisette-server...")
            if computer_cpu_platform == 'x86_64':
                r = requests.get(
                    "https://github.com/vyvir/althea/releases/download/v0.5.0/anisette-server-x86_64",
                    allow_redirects=True,
                )
            elif computer_cpu_platform == "aarch64":
                #Thanks, Dadoum for the anisette server!
                #or vyvir, do not forget to upload ur version of server.
                r = requests.get(
                    "https://github.com/vyvir/althea/releases/download/v0.5.0/anisette-server-aarch64",
                    allow_redirects=True
                )
                #sorry i dont know what will arm32 output
            elif computer_cpu_platform.find('v7') != -1 or computer_cpu_platform.find('ARM') != -1 or computer_cpu_platform.find('hf') != -1:
                r = requests.get(
                    "https://github.com/vyvir/althea/releases/download/v0.5.0/anisette-server-armv7",
                    allow_redirects=True
                )
            else:
                print('WARNING: YOUR CPU IS NOT SUPPORTED, THE PROGRAM MAY NOT WORK!')
                #ooops, just download x86-64 ver
                r = requests.get(
                    "https://github.com/vyvir/althea/releases/download/v0.5.0/anisette-server-x86_64",
                    allow_redirects=True,
                )
            open(f"{(altheapath)}/anisette-server", "wb").write(r.content)
            subprocess.run(f"chmod +x {(altheapath)}/anisette-server", shell=True)
            subprocess.run(f"chmod 755 {(altheapath)}/anisette-server", shell=True)
            self.loadalthea.set_fraction(0.2)
            self.lbl1.set_text("Downloading Apple Music APK...")
            r = requests.get(
                "https://apps.mzstatic.com/content/android-apple-music-apk/applemusic.apk",
                allow_redirects=True,
            )
            open(f"{(altheapath)}/am.apk", "wb").write(r.content)
            os.makedirs(f"{(altheapath)}/lib/x86_64")
            self.loadalthea.set_fraction(0.3)
            self.lbl1.set_text("Extracting necessary libraries...")
            CheckRunB = subprocess.run(
                f'unzip -j "{(altheapath)}/am.apk" "lib/x86_64/libstoreservicescore.so" -d "{(altheapath)}/lib/x86_64"',
                shell=True,
            )
            CheckRunC = subprocess.run(
                f'unzip -j "{(altheapath)}/am.apk" "lib/x86_64/libCoreADI.so" -d "{(altheapath)}/lib/x86_64"',
                shell=True,
            )
            silent_remove(f"{(altheapath)}/am.apk")
            self.loadalthea.set_fraction(0.4)
        self.lbl1.set_text("Starting anisette-server...")
        subprocess.run(f"cd {(altheapath)} && ./anisette-server &", shell=True)#-n 127.0.0.1 -p 6969 &", shell=True
        self.loadalthea.set_fraction(0.5)
        finished = False
        while not finished:
            CheckRun5 = subprocess.run(command, shell=True)
            if CheckRun5.returncode == 0:
                finished = True
            else:
                sleep(1)
        if not os.path.isfile(f"{(altheapath)}/AltServer"):
            self.lbl1.set_text("Downloading AltServer...")
            self.loadalthea.set_fraction(0.6)
            
            """
            r = requests.get(
                "https://github.com/NyaMisty/AltServer-Linux/releases/download/v0.0.5/AltServer-x86_64",
                allow_redirects=True,
            )
            """
            if computer_cpu_platform == 'AMD64':
                r = requests.get(
                    "https://github.com/NyaMisty/AltServer-Linux/releases/download/v0.0.5/AltServer-x86_64",
                    allow_redirects=True,
                )
            elif computer_cpu_platform == 'aarch64':
                r = requests.get(
                    "https://github.com/NyaMisty/AltServer-Linux/releases/download/v0.0.5/AltServer-aarch64",
                    allow_redirects=True
                )
            elif computer_cpu_platform.find('v7') != -1 or computer_cpu_platform.find('ARM') != -1 or computer_cpu_platform.find('hf') != -1:
                r = requests.get(
                    "https://github.com/NyaMisty/AltServer-Linux/releases/download/v0.0.5/AltServer-armv7",
                    allow_redirects=True
                )
            else:
                print('WARNING: YOUR CPU IS NOT SUPPORTED, AltServer MAY NOT WORK!')
                #ooops, just download x86-64 ver
                r = requests.get(
                    "https://github.com/NyaMisty/AltServer-Linux/releases/download/v0.0.5/AltServer-x86_64",
                    allow_redirects=True,
                )
            open(f"{(altheapath)}/AltServer", "wb").write(r.content)
            subprocess.run(f"chmod +x {(altheapath)}/AltServer", shell=True)
            subprocess.run(f"chmod 755 {(altheapath)}/AltServer", shell=True)
        self.loadalthea.set_fraction(0.8)
        if not os.path.isfile(f"{(altheapath)}/AltStore.ipa"):
            self.lbl1.set_text("Downloading AltStore...")
            altstore_download("Download")
        else:
            self.lbl1.set_text("Checking latest AltStore version...")
            if not altstore_download("Check"):
                self.lbl1.set_text("Downloading new version of AltStore...")
                altstore_download("Download")
        self.lbl1.set_text("Starting AltServer...")
        self.loadalthea.set_fraction(1.0)
        subprocess.run(f"{(altheapath)}/AltServer &", shell=True)
        return 0


class Login(Gtk.Window):#
    def __init__(self):
        super().__init__(title="Login")
        self.present()
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_resizable(False)
        self.set_border_width(10)

        grid = Gtk.Grid()
        self.add(grid)

        label = Gtk.Label(label="Apple ID: ")
        label.set_justify(Gtk.Justification.LEFT)

        self.entry1 = Gtk.Entry()

        label1 = Gtk.Label(label="Password: ")
        label1.set_justify(Gtk.Justification.LEFT)

        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)
        global icon_name
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, icon_name)
        self.entry.connect("icon-press", self.on_icon_toggled)

        self.button = Gtk.Button.new_with_label("Login")
        self.button.connect("clicked", self.on_click_me_clicked)

        grid.add(label)
        grid.attach(self.entry1, 1, 0, 2, 1)
        grid.attach_next_to(label1, label, Gtk.PositionType.BOTTOM, 1, 2)
        grid.attach(self.entry, 1, 2, 1, 1)
        grid.attach_next_to(self.button, self.entry, Gtk.PositionType.RIGHT, 1, 1)

        silent_remove(f"{(altheapath)}/log.txt")

    def on_click_me_clicked1(self):
        self.realthread1 = threading.Thread(target=self.onclickmethread)
        self.realthread1.start()
        GLib.idle_add(self.install_process)

    def on_click_me_clicked(self, button):
        silent_remove(f"{(altheapath)}/log.txt")
        if not os.path.isfile(f"{(altheapath)}/saved.txt"):
            self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Do you want to save your login and password?",
            )
            dialog.format_secondary_text("This will allow you to login automatically.")
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                apple_id = self.entry1.get_text().lower()
                password = self.entry.get_text()
                f = open(f"{(altheapath)}/saved.txt", "x")
                f.write(apple_id)
                f.write(":")
                f.write(password)
                f.close()
            dialog.destroy()
        self.entry.set_progress_pulse_step(0.2)
        # Call self.do_pulse every 100 ms
        self.timeout_id = GLib.timeout_add(100, self.do_pulse, None)
        self.entry.set_editable(False)
        self.entry1.set_editable(False)
        self.button.set_sensitive(False)
        self.realthread1 = threading.Thread(target=self.onclickmethread)
        self.realthread1.start()
        GLib.idle_add(self.install_process)

    def onclickmethread(self):
        if ios_version() >= "15.0":
            global savedcheck
            global apple_id
            global password
            if not savedcheck:
                apple_id = self.entry1.get_text().lower()
                password = self.entry.get_text()
            UDID = subprocess.check_output("idevice_id -l", shell=True).decode().strip()
            global InsAltStore
            print(PATH)
            silent_remove(f"{(altheapath)}/log.txt")
            #f = open(f"{(altheapath)}/log.txt", "w")
            #f.close()
            if os.path.isdir(f'{ os.environ["HOME"] }/.adi'):
                rmtree(f'{ os.environ["HOME"] }/.adi')
            InsAltStoreCMD = f"""export ALTSERVER_ANISETTE_SERVER='http://127.0.0.1:6969' ; {(AltServer)} -u {UDID} -a {apple_id} -p {password} {PATH} > {("$HOME/.local/share/althea/log.txt")}"""
            InsAltStore = subprocess.Popen(
                InsAltStoreCMD,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                shell=True,
            )
        else:  # If the iOS version is lower than 15.0, AltServer-Linux won't run
            global Failmsg
            Failmsg = "iOS 15.0 or later is required."
            dialog2 = DialogExample3(self)
            dialog2.run()
            dialog2.destroy()
            self.destroy()

    def install_process(self):
        Installing = True
        WarnTime = 0
        TwoFactorTime = 0
        global InsAltStore
        while Installing:
            CheckIns = subprocess.run(
                f'grep -F "Could not" {(altheapath)}/log.txt', shell=True
            )
            CheckWarn = subprocess.run(
                f'grep -F "Are you sure you want to continue?" {(altheapath)}/log.txt',
                shell=True,
            )
            CheckSuccess = subprocess.run(
                f'grep -F "Notify: Installation Succeeded" {(altheapath)}/log.txt',
                shell=True,
            )
            Check2fa = subprocess.run(
                f'grep -F "Enter two factor code" {(altheapath)}/log.txt', shell=True
            )
            if CheckIns.returncode == 0:
                InsAltStore.terminate()
                Installing = False
                global Failmsg
                Failmsg = subprocess.check_output(
                    f"tail -6 {(altheapath)}/log.txt", shell=True
                ).decode()
                dialog2 = DialogExample3(self)
                dialog2.run()
                dialog2.destroy()
                self.destroy()
            elif CheckWarn.returncode == 0 and WarnTime == 0:
                Installing = False
                word = "Are you sure you want to continue?"
                # This fixes an issue where the warn window appears when it shouldn't
                with open(f"{(altheapath)}/log.txt", "r") as file:
                    # Read all content of the file
                    content = file.read()
                    # Check if a string present in the file
                    if word in content:
                        global Warnmsg
                        Warnmsg = subprocess.check_output(
                            f"tail -8 {('$HOME/.local/share/althea/log.txt')}",
                            shell=True,
                        ).decode()
                        dialog1 = DialogExample2(self)
                        response1 = dialog1.run()
                        if response1 == Gtk.ResponseType.OK:
                            dialog1.destroy()
                            InsAltStore.communicate(input=b"\n")
                            WarnTime = 1
                            Installing = True
                        elif response1 == Gtk.ResponseType.CANCEL:
                            dialog1.destroy()
                            os.system(f"pkill -TERM -P {InsAltStore.pid}")
                            self.cancel()
                    else:
                        WarnTime = 1
                        Installing = True
            elif Check2fa.returncode == 0 and TwoFactorTime == 0:
                Installing = False
                dialog = DialogExample(self)
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    vercode = dialog.entry2.get_text()
                    vercode = vercode + "\n"
                    vercodebytes = bytes(vercode.encode())
                    InsAltStore.communicate(input=vercodebytes)
                    TwoFactorTime = 1
                    dialog.destroy()
                    Installing = True
                elif response == Gtk.ResponseType.CANCEL:
                    TwoFactorTime = 1
                    os.system(f"pkill -TERM -P {InsAltStore.pid}")
                    self.cancel()
                    dialog.destroy()
                    self.destroy()
            elif CheckSuccess.returncode == 0:
                Installing = False
                self.success()
                self.destroy()

    def success(self):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Success!",
        )
        dialog.format_secondary_text("Operation completed")
        dialog.run()
        dialog.destroy()

    def cancel(self):
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Cancelled",
        )
        dialog.format_secondary_text("Operation cancelled by user")
        dialog.run()
        dialog.destroy()

    def do_pulse(self, user_data):
        self.entry.progress_pulse()
        return True

    def on_icon_toggled(self, widget, icon, event):
        global icon_name
        if icon_name == "changes-prevent-symbolic":
            icon_name = "changes-allow-symbolic"
            self.entry.set_visibility(True)
        elif icon_name == "changes-allow-symbolic":
            icon_name = "changes-prevent-symbolic"
            self.entry.set_visibility(False)
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, icon_name)

    #
    #def on_editable_toggled(self, widget):
    #    print("lol")


class PairWindow(Handy.Window):
    def __init__(self):
        super().__init__(title="Pair your device")
        self.present()
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_resizable(False)
        self.set_border_width(20)

        self.handle = Handy.WindowHandle()
        self.add(self.handle)

        self.hbox = Gtk.Box(spacing=5, orientation=Gtk.Orientation.VERTICAL)
        self.handle.add(self.hbox)

        self.hb = Handy.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.props.title = "Pair your device"
        self.hbox.pack_start(self.hb, False, True, 0)

        pixbuf = Gtk.IconTheme.get_default().load_icon(
            "phone-apple-iphone-symbolic", 48, 0
        )
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.show()
        image.set_margin_top(5)
        self.hbox.pack_start(image, True, True, 0)

        lbl1 = Gtk.Label(
            label="Please make sure your device is connected to the computer.\nPress 'Pair' to pair your device."
        )
        lbl1.set_property("margin_left", 15)
        lbl1.set_property("margin_right", 15)
        lbl1.set_margin_top(5)
        lbl1.set_justify(Gtk.Justification.CENTER)
        self.hbox.pack_start(lbl1, False, False, 0)

        button = Gtk.Button(label="Pair")
        button.connect("clicked", self.on_info_clicked)
        button.set_property("margin_left", 150)
        button.set_property("margin_right", 150)
        self.hbox.pack_start(button, False, False, 10)

        self.add(button)
        self.add(self.hbox)

    def on_info_clicked(self, widget):
        try:
            subprocess.run(["idevicepair pair"], shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(e.output)
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Accept the trust dialog on the screen of your device,\nthen press 'OK'.",
            )

            dialog.run()
        try:
            subprocess.run(
                ["idevicepair pair"], shell=True, check=True, capture_output=True
            )
            self.destroy()
            global lolcheck
            global PATH
            if lolcheck == "altstr":
                PATH = f"{(altheapath)}/AltStore.ipa"
                win1()
            elif lolcheck == "ipa":
                win2 = FileChooserWindow()
            global ipa_path_exists
            if ipa_path_exists == True:
                PATH = win2.PATHFILE
                win1()
                ipa_path_exists = False
            lolcheck = "lol"
        except subprocess.CalledProcessError as e:
            errormsg = e.output.decode("utf-8")
            dialog1 = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=(errormsg),
            )
            dialog1.run()
            dialog1.destroy()
        try:
            dialog.destroy()
        except:
            pass


class FileChooserWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="FileChooser Example")
        box = Gtk.Box()
        self.add(box)

        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.PATHFILE = dialog.get_filename()
            global ipa_path_exists
            ipa_path_exists = True
        elif response == Gtk.ResponseType.CANCEL:
            self.destroy()

        dialog.destroy()

    def add_filters(self, dialog):
        filter_ipa = Gtk.FileFilter()
        filter_ipa.set_name("IPA files")
        filter_ipa.add_pattern("*.ipa")
        dialog.add_filter(filter_ipa)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)


class DialogExample(Gtk.Dialog):
    def __init__(self, parent):
        if not savedcheck:
            super().__init__(title="Verification code", transient_for=parent, flags=0)
        else:
            super().__init__(title="Verification code", flags=0)

        self.set_resizable(False)
        self.set_border_width(10)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK,
        )

        labelhelp = Gtk.Label(label="Enter the verification \ncode on your device:")
        labelhelp.set_justify(Gtk.Justification.CENTER)

        self.entry2 = Gtk.Entry()

        box = self.get_content_area()
        box.add(labelhelp)
        box.add(self.entry2)

        self.show_all()
        self.present()
        self.entry2.grab_focus()


class DialogExample2(Gtk.Dialog):
    def __init__(self, parent):
        global Warnmsg
        super().__init__(title="Warning", transient_for=parent, flags=0)
        self.present()
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        self.set_resizable(False)
        self.set_border_width(10)

        labelhelp = Gtk.Label(label="Are you sure you want to continue?")
        labelhelp.set_justify(Gtk.Justification.CENTER)

        labelhelp1 = Gtk.Label(label=Warnmsg)
        labelhelp1.set_justify(Gtk.Justification.CENTER)
        labelhelp1.set_line_wrap(True)
        labelhelp1.set_max_width_chars(48)
        labelhelp1.set_selectable(True)

        box = self.get_content_area()
        box.add(labelhelp)
        box.add(labelhelp1)
        self.show_all()


class DialogExample3(Gtk.Dialog):
    def __init__(self, parent):
        global Failmsg
        super().__init__(title="Fail", transient_for=parent, flags=0)
        self.present()
        self.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.set_resizable(False)
        self.set_border_width(10)

        labelhelp = Gtk.Label(label="AltServer has failed.")
        labelhelp.set_justify(Gtk.Justification.CENTER)

        labelhelp1 = Gtk.Label(label=Failmsg)
        labelhelp1.set_justify(Gtk.Justification.CENTER)
        labelhelp1.set_line_wrap(True)
        labelhelp1.set_max_width_chars(48)
        labelhelp1.set_selectable(True)

        box = self.get_content_area()
        box.add(labelhelp)
        box.add(labelhelp1)
        self.show_all()


class Oops(Handy.Window):
    def __init__(self):
        super().__init__(title="Error")
        self.present()
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_resizable(False)
        self.set_size_request(450, 100)
        self.set_border_width(10)

        # WindowHandle
        handle = Handy.WindowHandle()
        self.add(handle)
        box = Gtk.VBox()
        vb = Gtk.VBox(spacing=0, orientation=Gtk.Orientation.VERTICAL)

        # Headerbar
        self.hb = Handy.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.props.title = "Error"
        vb.pack_start(self.hb, False, True, 0)

        pixbuf = Gtk.IconTheme.get_default().load_icon(
            "application-x-addon-symbolic", 48, 0
        )
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.show()
        image.set_margin_top(10)
        vb.pack_start(image, True, True, 0)

        lbl1 = Gtk.Label()
        lbl1.set_justify(Gtk.Justification.CENTER)
        lbl1.set_markup(
            "You don't have the AppIndicator extension installed.\nYou can download it on "
            '<a href="https://extensions.gnome.org/extension/615/appindicator-support/" '
            'title="GNOME Extensions">GNOME Extensions</a>.'
        )
        lbl1.set_property("margin_left", 15)
        lbl1.set_property("margin_right", 15)
        lbl1.set_margin_top(10)

        button = Gtk.Button(label="OK")
        button.set_property("margin_left", 125)
        button.set_property("margin_right", 125)
        button.connect("clicked", self.on_info_clicked2)

        handle.add(vb)
        vb.pack_start(lbl1, expand=False, fill=True, padding=0)
        vb.pack_start(button, False, False, 10)
        box.add(vb)
        self.add(box)
        self.show_all()

    def on_info_clicked2(self, widget):
        quitit()


class OopsInternet(Handy.Window):
    def __init__(self):
        super().__init__(title="Error")
        self.present()
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_resizable(False)
        self.set_size_request(450, 100)
        self.set_border_width(10)

        # WindowHandle
        handle = Handy.WindowHandle()
        self.add(handle)
        box = Gtk.VBox()
        vb = Gtk.VBox(spacing=0, orientation=Gtk.Orientation.VERTICAL)

        # Headerbar
        self.hb = Handy.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.props.title = "Error"
        vb.pack_start(self.hb, False, True, 0)

        pixbuf = Gtk.IconTheme.get_default().load_icon(
            "network-wireless-no-route-symbolic", 48, 0
        )
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.show()
        image.set_margin_top(10)
        vb.pack_start(image, True, True, 0)

        lbl1 = Gtk.Label(
            label="althea is unable to connect to the Internet.\nPlease connect to the Internet and restart althea."
        )
        lbl1.set_property("margin_left", 15)
        lbl1.set_property("margin_right", 15)
        lbl1.set_justify(Gtk.Justification.CENTER)
        lbl1.set_margin_top(10)

        button = Gtk.Button(label="OK")
        button.set_property("margin_left", 125)
        button.set_property("margin_right", 125)
        button.connect("clicked", self.on_info_clicked2)

        handle.add(vb)
        vb.pack_start(lbl1, expand=False, fill=True, padding=0)
        vb.pack_start(button, False, False, 10)
        box.add(vb)
        self.add(box)
        self.show_all()

    def on_info_clicked2(self, widget):
        quitit()

def main():
    GLib.set_prgname("althea")

    global altheapath
    #global file_name
    altheapath = os.path.expanduser("~/.local/share/althea")

    if not os.path.exists(altheapath):
        os.makedirs(altheapath)

    log_file_path = os.path.join(altheapath, "log.txt")
    if not os.path.isfile(log_file_path):
        with open(log_file_path, 'w') as f:
            f.write("")

    if Gtk.StatusIcon.is_embedded:
        if connectioncheck():
            global indicator
            indicator = appindicator.Indicator.new(
                "althea-tray-icon",
                resource_path("resources/1.png"),
                appindicator.IndicatorCategory.APPLICATION_STATUS,
            )
            indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
            indicator.set_menu(menu())
            indicator.set_status(appindicator.IndicatorStatus.PASSIVE)
            openwindow(SplashScreen)
        else:
            openwindow(OopsInternet)
    else:
        openwindow(Oops)

    Handy.init()
    Gtk.main()

# Call main
if __name__ == "__main__":
    main()
