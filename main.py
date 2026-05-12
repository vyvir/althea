#!/usr/bin/python
import os
import errno
from shutil import rmtree
import json
import urllib.request
from urllib.request import urlopen
import urllib.parse
import requests
import subprocess
import signal
import threading
import keyring
from time import sleep
import platform
from packaging import version

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

    installedcheck = subprocess.run("test -e /usr/lib/althea/althea", shell=True).returncode == 0
    base_path = "/usr/lib/althea" if installedcheck else os.path.abspath(".")


# Global variables
ipa_path_exists = False
savedcheck = False
InsAltStore = subprocess.Popen(
    "test", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
)
login_or_file_chooser = "login"
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
export_anisette = "export ALTSERVER_ANISETTE_SERVER='http://127.0.0.1:6969'"

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

# --- Sideloader (Dadoum) integration ------------------------------------------
# AltServer-Linux's signer omits/mis-formats the DER-encoded entitlements blob
# that XNU now requires; amfid accepts it but posix_spawn rejects with EBADEXEC.
# Dadoum's Sideloader is a Linux-native sideloader that authenticates with
# Apple ID, generates the cert + provisioning profile itself, signs with the
# modern code-signature format (DER entitlements, SHA-256 CD), and installs
# directly. We drive its CLI over a pty because it uses getpass().
import pty
import select
import fcntl

SIDELOADER_DIR = os.path.expanduser("~/.local/share/althea/sideloader")
SIDELOADER_BIN = os.path.join(SIDELOADER_DIR, "sideloader")
SIDELOADER_URL_X86_64 = "https://github.com/Dadoum/Sideloader/releases/download/1.0-pre4/sideloader-cli-x86_64-linux-gnu.zip"
SIDELOADER_URL_AARCH64 = "https://github.com/Dadoum/Sideloader/releases/download/1.0-pre4/sideloader-cli-aarch64-linux-gnu.zip"

def download_sideloader():
    """Download Sideloader CLI if not present."""
    if os.path.isfile(SIDELOADER_BIN) and os.access(SIDELOADER_BIN, os.X_OK):
        return True
    os.makedirs(SIDELOADER_DIR, exist_ok=True)
    url = SIDELOADER_URL_AARCH64 if computer_cpu_platform == "aarch64" else SIDELOADER_URL_X86_64
    arch_name = "aarch64" if computer_cpu_platform == "aarch64" else "x86_64"
    bin_in_zip = f"sideloader-cli-{arch_name}-linux-gnu"
    zip_path = os.path.join(SIDELOADER_DIR, "sl.zip")
    try:
        r = requests.get(url, allow_redirects=True, timeout=120)
        with open(zip_path, "wb") as f:
            f.write(r.content)
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extract(bin_in_zip, SIDELOADER_DIR)
        os.rename(os.path.join(SIDELOADER_DIR, bin_in_zip), SIDELOADER_BIN)
        os.chmod(SIDELOADER_BIN, 0o755)
        os.remove(zip_path)
        return True
    except Exception as e:
        print(f"[althea] sideloader download failed: {e}")
        return False

# Sideloader process state, shared between the install thread and the GTK loop
_sideloader_proc = None
_sideloader_master_fd = None
_sideloader_log_path = os.path.expanduser("~/.local/share/althea/log.txt")
_sideloader_suppress_exit_marker = False

def sideloader_send(line):
    """Write a line + newline to the sideloader subprocess via the pty master fd."""
    global _sideloader_master_fd
    if _sideloader_master_fd is None:
        return
    try:
        os.write(_sideloader_master_fd, (line + "\n").encode())
    except OSError:
        pass

def sideloader_terminate():
    global _sideloader_proc, _sideloader_master_fd, _sideloader_suppress_exit_marker
    _sideloader_suppress_exit_marker = True
    try:
        if _sideloader_proc and _sideloader_proc.poll() is None:
            _sideloader_proc.terminate()
    except Exception:
        pass
    if _sideloader_master_fd is not None:
        try:
            os.close(_sideloader_master_fd)
        except OSError:
            pass
        _sideloader_master_fd = None

def sideloader_run_interactive_capture(cmd_args, apple_id_str, password_str):
    """Run a sideloader command over a pty, feed Apple ID/password, return (returncode, output)."""
    master_fd, slave_fd = pty.openpty()
    env = os.environ.copy()
    env["TERM"] = "dumb"
    proc = subprocess.Popen(
        cmd_args,
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        close_fds=True, env=env, preexec_fn=os.setsid,
    )
    os.close(slave_fd)
    creds_sent = {"apple_id": False, "password": False}
    buf = b""
    output_chunks = []
    while True:
        try:
            r, _, _ = select.select([master_fd], [], [], 0.2)
        except (OSError, ValueError):
            break
        if r:
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            output_chunks.append(chunk)
            buf += chunk
            if len(buf) > 8192:
                buf = buf[-4096:]
            text = buf.decode("utf-8", errors="replace")
            if not creds_sent["apple_id"] and "Apple ID:" in text:
                os.write(master_fd, (apple_id_str + "\n").encode())
                creds_sent["apple_id"] = True
                buf = b""
            elif not creds_sent["password"] and "Password:" in text:
                os.write(master_fd, (password_str + "\n").encode())
                creds_sent["password"] = True
                buf = b""
        if proc.poll() is not None:
            try:
                while True:
                    chunk = os.read(master_fd, 4096)
                    if not chunk:
                        break
                    output_chunks.append(chunk)
            except OSError:
                pass
            break
    try:
        os.close(master_fd)
    except OSError:
        pass
    proc.wait()
    return proc.returncode, b"".join(output_chunks).decode("utf-8", errors="replace")

def sideloader_revoke_existing_cert(apple_id_str, password_str):
    """List and revoke the existing iOS Development certificate. Returns (ok, message)."""
    import re
    rc, output = sideloader_run_interactive_capture(
        [SIDELOADER_BIN, "cert", "list", "-i"], apple_id_str, password_str
    )
    # Strip ANSI escape codes before parsing
    output_plain = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
    serial_match = (
        re.search(r'serial number\s+`([0-9A-Fa-f]{8,})`', output_plain)
        or re.search(r'[Ss]erial[^:\n]*:\s*([0-9A-Fa-f]{8,})', output_plain)
    )
    if not serial_match:
        return False, f"Could not find a certificate serial number in:\n{output_plain[:500]}"
    serial = serial_match.group(1)
    rc2, out2 = sideloader_run_interactive_capture(
        [SIDELOADER_BIN, "cert", "revoke", "-i", serial], apple_id_str, password_str
    )
    if rc2 != 0:
        return False, f"Revoke failed (rc={rc2}):\n{out2[:500]}"
    return True, f"Revoked certificate {serial}"

def sideloader_start_install(ipa_path, apple_id, password):
    """Start `sideloader install -i <ipa>` over a pty in a background thread.
    Auto-feed the Apple ID and password prompts; tee everything to log.txt for
    install_process() to poll for state transitions."""
    global _sideloader_proc, _sideloader_master_fd, _sideloader_suppress_exit_marker
    if not (os.path.isfile(SIDELOADER_BIN) and os.access(SIDELOADER_BIN, os.X_OK)):
        with open(_sideloader_log_path, "w") as f:
            f.write("Could not find sideloader binary at " + SIDELOADER_BIN + "\n")
        return

    _sideloader_suppress_exit_marker = False
    # Truncate the log
    open(_sideloader_log_path, "w").close()

    master_fd, slave_fd = pty.openpty()
    _sideloader_master_fd = master_fd
    env = os.environ.copy()
    env["TERM"] = "dumb"
    _sideloader_proc = subprocess.Popen(
        [SIDELOADER_BIN, "install", "-i", ipa_path],
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        close_fds=True, env=env, preexec_fn=os.setsid,
    )
    os.close(slave_fd)

    def reader():
        creds_sent = {"apple_id": False, "password": False}
        buf = b""
        with open(_sideloader_log_path, "ab", buffering=0) as logf:
            while True:
                try:
                    r, _, _ = select.select([master_fd], [], [], 0.2)
                except (OSError, ValueError):
                    break
                if r:
                    try:
                        chunk = os.read(master_fd, 4096)
                    except OSError:
                        chunk = b""  # EIO: pty slave closed, treat as EOF
                    if not chunk:
                        break
                    logf.write(chunk)
                    buf += chunk
                    # Keep only the tail to keep prompt matching cheap
                    if len(buf) > 8192:
                        buf = buf[-4096:]
                    text = buf.decode("utf-8", errors="replace")
                    if not creds_sent["apple_id"] and "Apple ID:" in text:
                        sideloader_send(apple_id)
                        creds_sent["apple_id"] = True
                        buf = b""
                    elif not creds_sent["password"] and "Password:" in text:
                        sideloader_send(password)
                        creds_sent["password"] = True
                        buf = b""
                if _sideloader_proc.poll() is not None:
                    # Drain anything left
                    try:
                        while True:
                            chunk = os.read(master_fd, 4096)
                            if not chunk: break
                            logf.write(chunk)
                    except OSError:
                        pass
                    break
            # Write exit marker for every exit path, unless this install was
            # explicitly cancelled (e.g. to revoke-and-retry).
            if not _sideloader_suppress_exit_marker:
                _sideloader_proc.wait()
                rc = _sideloader_proc.returncode
                logf.write(f"\n[althea] sideloader exited rc={rc}\n".encode())
                if rc == 0:
                    logf.write(b"Notify: Installation Succeeded\n")
                else:
                    logf.write(b"Could not install via sideloader\n")
        try:
            os.close(master_fd)
        except OSError:
            pass

    threading.Thread(target=reader, daemon=True).start()
# ------------------------------------------------------------------------------

# --- iOS 17+ re-sign + reinstall path -----------------------------------------
# AltServer-Linux's signer omits/mis-formats the DER-encoded entitlements blob
# that XNU now requires; amfid accepts it but posix_spawn rejects with EBADEXEC
# (POSIX 85, "Bad executable"). We re-sign AltServer's freshly-built IPA with
# zsign (which writes a SHA-256-only CodeDirectory + valid DER entitlements)
# and re-install via pymobiledevice3, which overwrites the broken install.
ALTHEA_TMPDIR = "/tmp/althea_altserver_tmp"
ALTHEA_CAPTURE_STOP = threading.Event()

def _altserver_tmp_watcher():
    """Poll /tmp for AltServer's UUID-named temp dir containing a .app with
    embedded.mobileprovision and copy a snapshot to ALTHEA_TMPDIR before
    AltServer cleans up."""
    import re, glob, shutil
    uuid_re = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    while not ALTHEA_CAPTURE_STOP.is_set():
        try:
            for entry in os.listdir("/tmp"):
                if not uuid_re.match(entry):
                    continue
                src_root = os.path.join("/tmp", entry)
                if not os.path.isdir(src_root):
                    continue
                for app_dir in glob.glob(os.path.join(src_root, "*.app")):
                    prov = os.path.join(app_dir, "embedded.mobileprovision")
                    if not os.path.isfile(prov):
                        continue
                    dst = os.path.join(ALTHEA_TMPDIR, os.path.basename(app_dir))
                    if os.path.isdir(dst):
                        continue  # already captured
                    try:
                        shutil.copytree(app_dir, dst)
                        print(f"[althea] captured AltServer staged app -> {dst}")
                    except Exception as e:
                        print(f"[althea] capture failed: {e}")
        except Exception:
            pass
        ALTHEA_CAPTURE_STOP.wait(0.1)

def find_zsign():
    for p in ("/home/linuxbrew/.linuxbrew/bin/zsign", "/usr/local/bin/zsign", "/usr/bin/zsign"):
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    from shutil import which
    return which("zsign")

def find_pymobiledevice3():
    from shutil import which
    p = which("pymobiledevice3") or os.path.expanduser("~/.local/bin/pymobiledevice3")
    return p if os.path.isfile(p) else None

def find_altserver_p12():
    cert_dir = os.path.expanduser("~/.altserver/Certificates")
    if not os.path.isdir(cert_dir):
        return None
    p12s = sorted(
        (os.path.join(cert_dir, f) for f in os.listdir(cert_dir) if f.endswith(".p12")),
        key=os.path.getmtime,
        reverse=True,
    )
    return p12s[0] if p12s else None

def find_captured_altserver_artifacts():
    """Look in ALTHEA_TMPDIR for the .app folder AltServer just built."""
    if not os.path.isdir(ALTHEA_TMPDIR):
        return None, None
    for root, dirs, files in os.walk(ALTHEA_TMPDIR):
        for d in dirs:
            if d.endswith(".app"):
                app_path = os.path.join(root, d)
                prov = os.path.join(app_path, "embedded.mobileprovision")
                if os.path.isfile(prov):
                    return app_path, prov
    return None, None

def zsign_resign_and_install(status_cb=lambda s: None):
    """Returns (ok: bool, message: str)."""
    zsign = find_zsign()
    pmd3 = find_pymobiledevice3()
    cert = find_altserver_p12()
    app_path, prov = find_captured_altserver_artifacts()

    if not zsign:
        return False, "zsign not found in PATH"
    if not pmd3:
        return False, "pymobiledevice3 not found (pip3 install --user pymobiledevice3)"
    if not cert:
        return False, "AltServer cert (~/.altserver/Certificates/*.p12) not found"
    if not app_path or not prov:
        return False, f"Could not find AltServer's staged .app under {ALTHEA_TMPDIR}"

    out_ipa = "/tmp/althea_resigned.ipa"
    silent_remove(out_ipa)

    status_cb("Re-signing with zsign (iOS 17+ CodeDirectory)...")
    res = subprocess.run(
        [zsign, "-f", "-2", "-z", "5",
         "-k", cert, "-p", "",
         "-m", prov,
         "-o", out_ipa,
         app_path],
        capture_output=True, text=True,
    )
    if res.returncode != 0 or not os.path.isfile(out_ipa):
        return False, f"zsign failed (rc={res.returncode}):\n{res.stdout}\n{res.stderr}"

    status_cb("Installing re-signed IPA via pymobiledevice3...")
    res = subprocess.run(
        [pmd3, "apps", "install", out_ipa],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return False, f"pymobiledevice3 install failed (rc={res.returncode}):\n{res.stdout}\n{res.stderr}"

    return True, "Re-signed and reinstalled"
# ------------------------------------------------------------------------------

def menu():
    menu = Gtk.Menu()

    if notify():
        command_upd = Gtk.MenuItem(label="Download Update")
        command_upd.connect("activate", showurl)
        menu.append(command_upd)

        menu.append(Gtk.SeparatorMenuItem())

    commands = [
        ("About althea", on_abtdlg),
        #("Settings", lambda x: openwindow(SettingsWindow)),
        ("Install AltStore", altstoreinstall),
        ("Install an IPA file", altserverfile),
        ("Pair", lambda x: openwindow(PairWindow)),
        ("Restart AltServer", restart_altserver),
        ("Quit althea", lambda x: quitit())
    ]

    for label, callback in commands:
        command = Gtk.MenuItem(label=label)
        command.connect("activate", callback)
        menu.append(command)
        if label == "Settings":
            menu.append(Gtk.SeparatorMenuItem())

    CheckRun11 = subprocess.run(f"test -e /usr/lib/althea/althea", shell=True)
    if installedcheck:
        global command_six
        CheckRun12 = subprocess.run(
            f"test -e $HOME/.config/autostart/althea.desktop", shell=True
        )
        if CheckRun12.returncode == 0:
            command_six.set_active(True)
        command_six.connect("activate", launchatlogin1)
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(command_six)

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
    pairchecking = subprocess.run('idevicepair validate | grep -q "SUCCESS"', shell=True) # use validate instaed of pair, pair causes error -5 if already paired
    if pairchecking.returncode == 0:
        return False
    else:
        return True

def altstoreinstall(_):
    if version.parse(ios_version()) < version.parse("15.0"):
        global Warnmsg
        Warnmsg = f"""\niOS {ios_version()} is not supported by AltStore.\nThe lowest supported version is iOS 15.0.\nYou can still continue, but errors may occur.\n"""
        ios_dialog = WarningDialog(parent=None)
        ios_dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        ios_response = ios_dialog.run()
        if ios_response == Gtk.ResponseType.OK:
            ios_dialog.destroy()
            if paircheck():
                openwindow(PairWindow)
            else:
                win1()
        elif ios_response == Gtk.ResponseType.CANCEL:
            ios_dialog.destroy()
    else:
        if paircheck():
            openwindow(PairWindow)
        else:
            win1()


def altserverfile(_):
    if paircheck():
        global login_or_file_chooser
        login_or_file_chooser = "file_chooser"
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

def restart_altserver(_):
    subprocess.run(f"killall {AltServer}", shell=True)
    subprocess.run(f"killall {AnisetteServer}", shell=True)
    subprocess.run("idevicepair pair", shell=True)
    subprocess.run(
        f"""{export_anisette} ; {(altheapath)}/AltServer &""",
        shell=True,
    )

def use_saved_credentials():
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
        apple_id = keyring.get_password("althea", "apple_id")
        password = keyring.get_password("althea", "password")
        #print(apple_id, password)
        global savedcheck
        savedcheck = True
        Login().on_click_me_clicked1()
    else:
        apple_id = keyring.delete_password("althea", "apple_id")
        password = keyring.delete_password("althea", "password")
        win3 = Login()
        win3.show_all()
    dialog.destroy()

def win1():
    try:
        if keyring.get_password("althea", "apple_id"):
            use_saved_credentials()
        else:
            openwindow(Login)
    except keyring.errors.KeyringError:
        openwindow(Login)

def win2(_):
    try:
        if keyring.get_password("althea", "apple_id"):
            use_saved_credentials()
        else:
            openwindow(Login)
    except keyring.errors.KeyringError:
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
            self.show_main_ui()
        else:
            GLib.timeout_add(200, self.wait_for_t, self.t)

    def show_main_ui(self):
        # Replace the loading widgets with action buttons so the app
        # is usable even when the AppIndicator tray isn't visible.
        self.set_title("althea")
        self.lbl1.destroy()
        self.loadalthea.destroy()

        actions = [
            ("About althea", on_abtdlg),
            ("Install AltStore", altstoreinstall),
            ("Install an IPA file", altserverfile),
            ("Pair", lambda x: openwindow(PairWindow)),
            ("Restart AltServer", restart_altserver),
            ("Quit althea", lambda x: quitit()),
        ]
        for label, callback in actions:
            btn = Gtk.Button(label=label)
            btn.set_property("margin_left", 40)
            btn.set_property("margin_right", 40)
            btn.connect("clicked", callback)
            self.mainBox.pack_start(btn, False, False, 2)

        self.connect("destroy", lambda *_: quitit())
        self.show_all()

    def download_bin(self, name, link):
        match computer_cpu_platform:
            case 'x86_64':
                r = requests.get(
                    f"{link}-x86_64",
                    allow_redirects=True,
                )
            case 'aarch64':
                r = requests.get(
                    f"{link}-aarch64",
                    allow_redirects=True
                )
            case _:
                if computer_cpu_platform.find('v7') != -1 \
                    or computer_cpu_platform.find('ARM') != -1 \
                        or computer_cpu_platform.find('hf') != -1:
                            r = requests.get(
                                f"{link}-armv7",
                                allow_redirects=True
                            )
                else:
                    self.lbl1.set_text('Could not identify the CPU architecture, downloading the x86_64 version...')
                    r = requests.get(
                        f"{link}-x86_64",
                        allow_redirects=True,
                    )
        open(f"{(altheapath)}/{name}", "wb").write(r.content)
        subprocess.run(f"chmod +x {(altheapath)}/{name}", shell=True)
        subprocess.run(f"chmod 755 {(altheapath)}/{name}", shell=True)

    
    def startup_process(self):
        self.lbl1.set_text("Checking if anisette-server is already running...")
        self.loadalthea.set_fraction(0.1)
        command = 'curl 127.0.0.1:6969 | grep -q "{"'
        CheckRun = subprocess.run(command, shell=True)
        if not os.path.isfile(f"{(altheapath)}/anisette-server"):
            self.lbl1.set_text("Downloading anisette-server...")
            self.download_bin("anisette-server", "https://github.com/vyvir/althea/releases/download/v0.5.0/anisette-server")
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
        subprocess.run(f"{(altheapath)}/anisette-server -n 127.0.0.1 -p 6969 &", shell=True)
        #subprocess.run(f"cd {(altheapath)} && ./anisette-server &", shell=True)#-n 127.0.0.1 -p 6969 &", shell=True
        self.loadalthea.set_fraction(0.5)
        finished = False
        while not finished:
            CheckRun5 = subprocess.run(command, shell=True)
            if CheckRun5.returncode == 0:
                finished = True
            else:
                sleep(1)
        if not os.path.isfile(f"{(altheapath)}/AltServer"):
            self.download_bin("AltServer", "https://github.com/datspike/AltServer-Linux/releases/download/v0.1.1/AltServer")
            self.lbl1.set_text("Downloading AltServer...")
            self.loadalthea.set_fraction(0.6)
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
        self.loadalthea.set_fraction(0.95)
        subprocess.run(f"{export_anisette} ; {(altheapath)}/AltServer &", shell=True)
        # Download Sideloader (Dadoum) — the modern signer used by althea's
        # "Install" path, since AltServer-Linux signatures are rejected by iOS 17+.
        if not (os.path.isfile(SIDELOADER_BIN) and os.access(SIDELOADER_BIN, os.X_OK)):
            self.lbl1.set_text("Downloading Sideloader...")
            download_sideloader()
        self.loadalthea.set_fraction(1.0)
        return 0


class Login(Gtk.Window):
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
        self.hide()
        self.realthread1 = threading.Thread(target=self.onclickmethread)
        self.realthread1.start()
        GLib.idle_add(self.install_process)

    def on_click_me_clicked(self, button):
        silent_remove(f"{(altheapath)}/log.txt")
        try:
            if not keyring.get_password("althea", "apple_id"):
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
                    keyring.set_password("althea", "apple_id", apple_id)
                    keyring.set_password("althea", "password", password)
                dialog.destroy()
        except keyring.errors.KeyringError:
            pass
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
            print(PATH)
            silent_remove(f"{(altheapath)}/log.txt")
            # Hand off to Dadoum's Sideloader (drives prompts via pty).
            # Resolve the IPA path: althea uses literal "$HOME/..." in PATH for
            # the AltStore.ipa case; expand env vars so sideloader gets a real path.
            ipa_resolved = os.path.expandvars(PATH)
            sideloader_start_install(ipa_resolved, apple_id, password)
        else:
            global Failmsg
            Failmsg = "iOS 15.0 or later is required."
            dialog2 = FailDialog(self)
            dialog2.run()
            dialog2.destroy()
            self.destroy()

    def install_process(self):
        # Bootstrap state and switch to the timeout-driven step (so the GTK
        # main loop stays responsive while sideloader runs).
        self._install_two_factor_done = False
        self._install_log = f"{(altheapath)}/log.txt"
        if not os.path.exists(self._install_log):
            open(self._install_log, "a").close()
        GLib.timeout_add(250, self._install_step)
        return False  # don't reschedule from idle_add

    def _install_step(self):
        log_path = self._install_log

        # Handle "existing certificate" error (7460) before the generic failure check.
        Check7460 = subprocess.run(
            f'grep -F "statusCode = 7460" {log_path} 2>/dev/null', shell=True
        )
        if Check7460.returncode == 0 and not getattr(self, '_cert_revoke_attempted', False):
            sideloader_terminate()
            self._cert_revoke_attempted = True
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Existing iOS Development certificate found",
            )
            dialog.format_secondary_text(
                "Your Apple ID already has an iOS Development certificate.\n"
                "Do you want to revoke it and retry the installation?"
            )
            response = dialog.run()
            dialog.destroy()
            if response == Gtk.ResponseType.YES:
                open(_sideloader_log_path, "w").close()
                def revoke_and_retry():
                    ok, msg = sideloader_revoke_existing_cert(apple_id, password)
                    if ok:
                        open(_sideloader_log_path, "w").close()
                        ipa_resolved = os.path.expandvars(PATH)
                        sideloader_start_install(ipa_resolved, apple_id, password)
                    else:
                        with open(_sideloader_log_path, "a") as f:
                            f.write(f"Could not revoke certificate: {msg}\n")
                    GLib.idle_add(self.install_process)
                threading.Thread(target=revoke_and_retry, daemon=True).start()
            else:
                self.cancel()
                self.destroy()
            return False

        CheckIns = subprocess.run(
            f'grep -F "Could not" {log_path} 2>/dev/null', shell=True
        )
        CheckSuccess = subprocess.run(
            f'grep -F "Notify: Installation Succeeded" {log_path} 2>/dev/null',
            shell=True,
        )
        Check2fa = subprocess.run(
            f'grep -F "code has been sent to your devices" {log_path} 2>/dev/null',
            shell=True,
        )

        if CheckIns.returncode == 0:
            sideloader_terminate()
            global Failmsg
            Failmsg = subprocess.check_output(
                f"tail -10 {log_path}", shell=True
            ).decode()
            dialog2 = FailDialog(self)
            dialog2.run()
            dialog2.destroy()
            self.destroy()
            return False  # stop polling
        if Check2fa.returncode == 0 and not self._install_two_factor_done:
            self._install_two_factor_done = True
            dialog = VerificationDialog(self)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                vercode = dialog.entry2.get_text()
                sideloader_send(vercode)
                dialog.destroy()
                return True  # keep polling
            else:
                sideloader_terminate()
                self.cancel()
                dialog.destroy()
                self.destroy()
                return False
        if CheckSuccess.returncode == 0:
            self.success()
            self.destroy()
            return False
        return True  # keep polling

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
            global login_or_file_chooser
            global PATH
            if login_or_file_chooser == "file_chooser":
                win2 = FileChooserWindow()
            else:
                PATH = f"{(altheapath)}/AltStore.ipa"
                win1()
            global ipa_path_exists
            if ipa_path_exists == True:
                PATH = win2.PATHFILE
                win1()
                ipa_path_exists = False
            login_or_file_chooser = "login"
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
        super().__init__(title="File chooser")
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


class VerificationDialog(Gtk.Dialog):
    def __init__(self, parent):
        if not savedcheck:
            super().__init__(title="Verification code", transient_for=parent, flags=0)
        else:
            super().__init__(title="Verification code", flags=0)
        self.present()
        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )
        self.set_resizable(True)
        self.set_border_width(10)

        labelhelp = Gtk.Label(
            label="Enter the verification \ncode on your device: "
        )
        labelhelp.set_justify(Gtk.Justification.CENTER)

        self.entry2 = Gtk.Entry()

        box = self.get_content_area()
        box.add(labelhelp)
        box.add(self.entry2)
        self.show_all()


class WarningDialog(Gtk.Dialog):
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


class FailDialog(Gtk.Dialog):
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
    def __init__(self, markup_text, pixbuf_icon):
        super().__init__(title="Error")
        self.present()
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_resizable(False)
        self.set_size_request(450, 100)
        self.set_border_width(10)

        # WindowHandle
        handle = Handy.WindowHandle()
        self.add(handle)
        vb = Gtk.VBox(spacing=0, orientation=Gtk.Orientation.VERTICAL)

        # Headerbar
        self.hb = Handy.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.props.title = "Error"
        vb.pack_start(self.hb, False, True, 0)

        pixbuf = Gtk.IconTheme.get_default().load_icon(
            pixbuf_icon, 48, 0
        )
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.show()
        image.set_margin_top(10)
        vb.pack_start(image, True, True, 0)

        lbl1 = Gtk.Label()
        lbl1.set_justify(Gtk.Justification.CENTER)
        lbl1.set_markup(markup_text)
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
        self.show_all()

    def on_info_clicked2(self, widget):
        quitit()

class SettingsWindow(Handy.Window):
    def __init__(self):
        super().__init__(title="Settings")
        self.present()
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_resizable(False)
        #self.set_size_request(450, 100)
        self.set_border_width(10)

        # WindowHandle
        handle = Handy.WindowHandle()
        self.add(handle)
        vb = Gtk.VBox(spacing=0, orientation=Gtk.Orientation.VERTICAL)

        # Headerbar
        self.hb = Handy.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.props.title = "Settings"
        vb.pack_start(self.hb, False, True, 0)

        pixbuf = Gtk.IconTheme.get_default().load_icon(
            "emblem-system-symbolic", 48, 0
        )
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.show()
        image.set_margin_top(10)
        vb.pack_start(image, True, True, 0)

        lbl1 = Gtk.Label()
        lbl1.set_justify(Gtk.Justification.CENTER)
        lbl1.set_markup(
            "These settings are experimental. Use at own risk."
        )
        lbl1.set_property("margin_left", 15)
        lbl1.set_property("margin_right", 15)
        lbl1.set_margin_top(10)

        button = Gtk.Button(label="OK")
        button.set_property("margin_left", 125)
        button.set_property("margin_right", 125)
        button.connect("clicked", self.on_info_clicked2)

        button1 = Gtk.Button(label="Open PairWindow")
        button1.set_property("margin_left", 125)
        button1.set_property("margin_right", 125)
        button1.connect("clicked", self.on_info_clicked3)

        handle.add(vb)
        vb.pack_start(lbl1, expand=False, fill=True, padding=0)
        vb.pack_start(button, False, False, 10)
        vb.pack_start(button1, False, False, 10)
        self.show_all()

    def on_info_clicked2(self, widget):
        self.destroy()

    def on_info_clicked3(self, widget):
        openwindow(PairWindow)


# -----------------------------------------------------------------------------

# Main function
def main():
    GLib.set_prgname("althea")  # Sets the global program name
    global altheapath
    #global file_name
    if not os.path.exists(altheapath):  # Creates $HOME/.local/share/althea
        os.mkdir(altheapath)
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
        markup_text = "althea is unable to connect to the Internet.\nPlease connect to the Internet and restart althea."
        pixbuf_icon = "network-wireless-no-route-symbolic"
        Oops(markup_text, pixbuf_icon)  # Notify the user there is no Internet connection
    Handy.init()
    Gtk.main()

# Call main
if __name__ == "__main__":
    main()
