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
    installedcheck = subprocess.run("test -e /usr/lib/althea/althea", shell=True).returncode == 0
    base_path = "/usr/lib/althea" if installedcheck else os.path.abspath(".")
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

    if notify():
        command_upd = Gtk.MenuItem(label="Download Update")
        command_upd.connect("activate", showurl)
        menu.append(command_upd)
        menu.append(Gtk.SeparatorMenuItem())

    commands = [
        ("About althea", on_abtdlg),
        ("Install AltStore", altstoreinstall),
        ("Install an IPA file", altserverfile),
        ("Pair", lambda x: openwindow(PairWindow)),
        ("Restart AltServer", restartaltserver)
    ]

    for label, callback in commands:
        command = Gtk.MenuItem(label=label)
        command.connect("activate", callback)
        menu.append(command)
        menu.append(Gtk.SeparatorMenuItem())

    if subprocess.run("test -e /usr/lib/althea/althea", shell=True).returncode == 0:
        global command_six
        if subprocess.run("test -e $HOME/.config/autostart/althea.desktop", shell=True).returncode == 0:
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

def kill_processes():
    for process in [AltServer, AnisetteServer]:
        subprocess.run(["killall", process], check=False)

def quitit():
    kill_processes()
    Gtk.main_quit()
    os.kill(os.getpid(), signal.SIGKILL)

def restartaltserver(_):
    kill_processes()
    subprocess.run("idevicepair pair", shell=True, check=False)
    subprocess.Popen(
        f"{altheapath}/AltServer",
        env=dict(os.environ, ALTSERVER_ANISETTE_SERVER='http://127.0.0.1:6969'),
        shell=True
    )

def winerm():
    silent_remove(f"{altheapath}/log.txt")
    dialog = Gtk.MessageDialog(
        flags=0,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text="Do you want to login automatically?",
    )
    dialog.format_secondary_text("Your login and password have been saved earlier.")
    response = dialog.run()

    if response == Gtk.ResponseType.YES:
        try:
            with open(f"{altheapath}/saved.txt", "r") as f:
                for line in f:
                    if 'ł' in line:
                        global apple_id, password, savedcheck
                        apple_id, password = line.split("ł")
                        savedcheck = True
                        Login().on_click_me_clicked1()
                        break
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}")
    else:
        silent_remove(f"{altheapath}/saved.txt")
        Login().show_all()

    dialog.destroy()

def win1():
    winerm() if os.path.isfile(f"{altheapath}/saved.txt") else openwindow(Login)

def win2(_):
    win1()

def actionCallback(notification, action, user_data=None):
    Gtk.show_uri_on_window(None, "https://github.com/vyvir/althea/releases", Gdk.CURRENT_TIME)
    quitit()

def launchatlogin1(_):
    if command_six.get_active():
        os.popen(AutoStart).read()
        return True
    silent_remove("$HOME/.config/autostart/althea.desktop")
    return False

def silent_remove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

def altstore_download(value):
    baseUrl = "https://cdn.altstore.io/file/altstore/apps.json"
    response = requests.get(baseUrl)

    if response.status_code == 200:
        data = response.json()
        for app in data['apps']:
            if app['name'] == "AltStore":
                if value == "Check":
                    size = app['versions'][0]['size']
                    return size == os.path.getsize(f'{altheapath}/AltStore.ipa')
                elif value == "Download":
                    latest = app['versions'][0]['downloadURL']
                    r = requests.get(latest, allow_redirects=True)
                    latest_filename = latest.split('/')[-1]
                    with open(f"{altheapath}/{latest_filename}", "wb") as f:
                        f.write(r.content)
                    os.rename(f"{altheapath}/{latest_filename}", f"{altheapath}/AltStore.ipa")
                    subprocess.run(["chmod", "755", f"{altheapath}/AltStore.ipa"])
                return True
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
        self.setup_window()
        self.create_ui()
        self.start_startup_process()

    def setup_window(self):
        self.set_resizable(False)
        self.set_default_size(512, 288)
        self.present()
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_keep_above(True)

    def create_ui(self):
        self.mainBox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.add(self.mainBox)

        image = self.create_image()
        self.mainBox.pack_start(image, False, True, 0)

        self.lbl1 = Gtk.Label(label="Starting althea...")
        self.mainBox.pack_start(self.lbl1, False, False, 6)

        self.loadalthea = Gtk.ProgressBar()
        self.mainBox.pack_start(self.loadalthea, True, True, 0)

    def create_image(self):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join("resources/4.png"),
            width=512, height=288, preserve_aspect_ratio=False
        )
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.show()
        return image

    def start_startup_process(self):
        self.t = threading.Thread(target=self.startup_process)
        self.t.start()
        GLib.timeout_add(200, self.check_thread)

    def check_thread(self):
        if not self.t.is_alive():
            global indicator
            indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
            self.t.join()
            self.destroy()
            return False
        return True

    def startup_process(self):
        steps = [
            (self.check_anisette_server, "Checking if anisette-server is already running...", 0.1),
            (self.setup_anisette_server, "Setting up anisette-server if not installed...", 0.3),
            (self.download_apple_music_apk, "Downloading Apple Music APK if necessary...", 0.4),
            (self.extract_libraries, "Extracting necessary libraries if needed...", 0.5),
            (self.start_anisette_server, "Starting anisette-server...", 0.6),
            (self.setup_altserver, "Setting up AltServer if not installed...", 0.8),
            (self.start_altserver, "Starting AltServer...", 1.0)
        ]

        for step, message, progress in steps:
            GLib.idle_add(self.lbl1.set_text, message)
            GLib.idle_add(self.loadalthea.set_fraction, progress)
            step()

    def check_anisette_server(self):
        command = 'curl -s 127.0.0.1:6969 | grep -q "{"'
        result = subprocess.run(command, shell=True)
        return result.returncode == 0

    def setup_anisette_server(self):
        anisette_path = f"{altheapath}/anisette-server"
        if os.path.isfile(anisette_path):
            print("Anisette server already installed.")
            return
        print("Installing Anisette server...")
        urls = {
            'x86_64': "https://github.com/vyvir/althea/releases/download/v0.5.0/anisette-server-x86_64",
            'aarch64': "https://github.com/vyvir/althea/releases/download/v0.5.0/anisette-server-aarch64",
            'armv7': "https://github.com/vyvir/althea/releases/download/v0.5.0/anisette-server-armv7",
        }
        cpu_url = urls.get(computer_cpu_platform, urls['x86_64'])
        self.download_file(cpu_url, anisette_path)
        self.run_command(f"chmod +x {anisette_path}")
        self.run_command(f"chmod 755 {anisette_path}")

    def download_apple_music_apk(self):
        apk_path = f"{altheapath}/am.apk"
        if os.path.isfile(apk_path):
            print("Apple Music APK already downloaded.")
            return
        print("Downloading Apple Music APK...")
        url = "https://apps.mzstatic.com/content/android-apple-music-apk/applemusic.apk"
        self.download_file(url, apk_path)

    def extract_libraries(self):
        lib_path = f"{altheapath}/lib/x86_64/libstoreservicescore.so"
        if os.path.isfile(lib_path):
            print("Libraries already extracted.")
            return
        print("Extracting libraries...")
        os.makedirs(f"{altheapath}/lib/x86_64", exist_ok=True)
        self.run_command(f'unzip -j "{altheapath}/am.apk" "lib/x86_64/libstoreservicescore.so" -d "{altheapath}/lib/x86_64"')
        self.run_command(f'unzip -j "{altheapath}/am.apk" "lib/x86_64/libCoreADI.so" -d "{altheapath}/lib/x86_64"')
        os.remove(f"{altheapath}/am.apk")

    def start_anisette_server(self):
        print("Starting Anisette server...")
        self.run_command(f"cd {altheapath} && ./anisette-server &")
        for _ in range(30):
            if self.check_anisette_server():
                break
            sleep(1)
        else:
            print("Failed to start anisette-server")

    def setup_altserver(self):
        altserver_path = f"{altheapath}/AltServer"
        if os.path.isfile(altserver_path):
            print("AltServer already installed.")
            return
        print("Installing AltServer...")
        altserver_urls = {
            'AMD64': "https://github.com/NyaMisty/AltServer-Linux/releases/download/v0.0.5/AltServer-x86_64",
            'aarch64': "https://github.com/NyaMisty/AltServer-Linux/releases/download/v0.0.5/AltServer-aarch64",
            'armv7': "https://github.com/NyaMisty/AltServer-Linux/releases/download/v0.0.5/AltServer-armv7",
        }
        altserver_url = altserver_urls.get(computer_cpu_platform, altserver_urls['AMD64'])
        self.download_file(altserver_url, altserver_path)
        self.run_command(f"chmod +x {altserver_path}")
        self.run_command(f"chmod 755 {altserver_path}")

    def start_altserver(self):
        print("Starting AltServer...")
        self.run_command(f"{altheapath}/AltServer &")

    def download_file(self, url, destination):
        if os.path.isfile(destination):
            print(f"File {destination} already exists.")
            return
        try:
            r = requests.get(url, allow_redirects=True)
            r.raise_for_status()
            with open(destination, "wb") as f:
                f.write(r.content)
        except requests.RequestException as e:
            print(f"Error downloading file: {e}")

    def run_command(self, command):
        subprocess.run(command, shell=True)


class Login(Gtk.Window):
    def __init__(self):
        super().__init__(title="Login")
        self.setup_window()
        self.create_ui()

    def setup_window(self):
        self.present()
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_resizable(False)
        self.set_border_width(10)

    def create_ui(self):
        grid = Gtk.Grid()
        self.add(grid)

        self.entry1 = self.create_entry("Apple ID: ", grid, 0)
        self.entry = self.create_password_entry("Password: ", grid, 2)

        self.button = Gtk.Button.new_with_label("Login")
        self.button.connect("clicked", self.on_click_me_clicked)
        grid.attach_next_to(self.button, self.entry, Gtk.PositionType.RIGHT, 1, 1)

    def create_entry(self, label_text, grid, row):
        label = Gtk.Label(label=label_text)
        label.set_justify(Gtk.Justification.LEFT)
        entry = Gtk.Entry()
        grid.add(label)
        grid.attach(entry, 1, row, 2, 1)
        return entry

    def create_password_entry(self, label_text, grid, row):
        entry = self.create_entry(label_text, grid, row)
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "changes-prevent-symbolic")
        entry.connect("icon-press", self.on_icon_toggled)
        return entry

    def on_click_me_clicked(self, button):
        self.save_credentials_dialog()
        self.start_login_process()

    def save_credentials_dialog(self):
        if not os.path.isfile(f"{altheapath}/saved.txt"):
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Do you want to save your login and password?"
            )
            dialog.format_secondary_text("This will allow you to log in automatically.")
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                self.save_credentials()
            dialog.destroy()

    def save_credentials(self):
        apple_id = self.entry1.get_text().lower()
        password = self.entry.get_text()
        with open(f"{altheapath}/saved.txt", "w") as f:
            f.write(f"{apple_id}:{password}")

    def start_login_process(self):
        self.entry.set_progress_pulse_step(0.2)
        self.timeout_id = GLib.timeout_add(100, self.do_pulse, None)
        self.entry.set_editable(False)
        self.entry1.set_editable(False)
        self.button.set_sensitive(False)
        self.realthread1 = threading.Thread(target=self.onclickmethread)
        self.realthread1.start()
        GLib.idle_add(self.install_process)


    def onclickmethread(self):
        global apple_id, password

        if not savedcheck:
            apple_id = self.entry1.get_text().lower()
            password = self.entry.get_text()
        else:
            with open(f"{altheapath}/saved.txt", "r") as f:
                saved_data = f.read().strip()
                if ":" in saved_data:
                    apple_id, password = saved_data.split(":", 1)
                else:
                    print("Invalid saved credentials format.")
                    return

        if ios_version() >= "15.0":
            try:
                UDID = subprocess.check_output("idevice_id -l", shell=True).decode().strip()
            except subprocess.CalledProcessError as e:
                print(f"Error obtaining UDID: {e}")
                return

            silent_remove(f"{altheapath}/log.txt")

            if os.path.isdir(f'{os.environ["HOME"]}/.adi'):
                rmtree(f'{os.environ["HOME"]}/.adi')

            InsAltStoreCMD = f"""export ALTSERVER_ANISETTE_SERVER='http://127.0.0.1:6969' ; {AltServer} -u {UDID} -a {apple_id} -p {password} {PATH} > {os.environ["HOME"]}/.local/share/althea/log.txt"""
            try:
                global InsAltStore
                InsAltStore = subprocess.Popen(
                    InsAltStoreCMD,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    shell=True,
                )
            except Exception as e:
                print(f"Error starting subprocess: {e}")
        else:
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
                f'grep -F "Could not" {altheapath}/log.txt', shell=True
            )
            CheckWarn = subprocess.run(
                f'grep -F "Are you sure you want to continue?" {altheapath}/log.txt', shell=True
            )
            CheckSuccess = subprocess.run(
                f'grep -F "Notify: Installation Succeeded" {altheapath}/log.txt', shell=True
            )
            Check2fa = subprocess.run(
                f'grep -F "Enter two factor code" {altheapath}/log.txt', shell=True
            )

            if CheckIns.returncode == 0:
                InsAltStore.terminate()
                Installing = False
                global Failmsg
                Failmsg = subprocess.check_output(f"tail -6 {altheapath}/log.txt", shell=True).decode()
                dialog2 = DialogExample3(self)
                dialog2.run()
                dialog2.destroy()
                self.destroy()

            elif CheckWarn.returncode == 0 and WarnTime == 0:
                Installing = False
                word = "Are you sure you want to continue?"
                with open(f"{altheapath}/log.txt", "r") as file:
                    content = file.read()
                    if word in content:
                        global Warnmsg
                        Warnmsg = subprocess.check_output(f"tail -8 {os.environ['HOME']}/.local/share/althea/log.txt", shell=True).decode()
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
                    vercode = dialog.entry2.get_text().strip() + "\n"
                    print(f"2FA Code: {vercode}")
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
            visibility = True
        else:
            icon_name = "changes-prevent-symbolic"
            visibility = False

        self.entry.set_visibility(visibility)
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
        filters = [
            ("IPA files", "*.ipa"),
            ("Any files", "*")
        ]

        for name, pattern in filters:
            filter = Gtk.FileFilter()
            filter.set_name(name)
            filter.add_pattern(pattern)
            dialog.add_filter(filter)

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
