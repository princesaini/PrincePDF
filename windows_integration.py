"""
PrincePDF - Windows 11 Integration & Default App Registration
Handles Windows Registry file association for .pdf, Default Apps registration,
desktop shortcut creation, and launching Windows Default App settings.
"""

import os
import sys
import subprocess
import winreg
from typing import Tuple, Optional


PROGID = "PrincePDF.Document"
APP_NAME = "PrincePDF"
APP_DESC = "PrincePDF - Fast, modern, and minimalist PDF viewer for Windows 11."


def get_pythonw_path() -> str:
    """Returns path to pythonw.exe to avoid console popup on Windows."""
    exe = sys.executable
    dir_name = os.path.dirname(exe)
    pythonw = os.path.join(dir_name, "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return exe


def get_executable_path() -> str:
    """Returns path to PrincePDF.exe if available, otherwise pythonw.exe."""
    if getattr(sys, "frozen", False):
        return sys.executable
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_exe = os.path.join(current_dir, "PrincePDF.exe")
    if os.path.exists(root_exe):
        return root_exe
    dist_exe = os.path.join(current_dir, "dist", "PrincePDF.exe")
    if os.path.exists(dist_exe):
        return dist_exe
    return get_pythonw_path()


def get_icon_path() -> str:
    """Returns path to app icon (.ico)."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            ico = os.path.join(meipass, "resources", "app_icon.ico")
            if os.path.exists(ico):
                return ico
        return sys.executable
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ico = os.path.join(current_dir, "resources", "app_icon.ico")
    if os.path.exists(ico):
        return ico
    return ""


def get_png_icon_path() -> str:
    """Returns path to 1024x1024 master PNG icon for crisp high-DPI UI rendering."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            png = os.path.join(meipass, "resources", "app_icon.png")
            if os.path.exists(png):
                return png
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for name in ["app_icon.png", "app_icon_512.png", "app_icon_256.png"]:
        p = os.path.join(current_dir, "resources", name)
        if os.path.exists(p):
            return p
    return get_icon_path()


def get_open_command() -> str:
    """Command string executed by Windows when opening a PDF."""
    target_exe = get_executable_path()
    if target_exe.lower().endswith(".exe") and not target_exe.lower().endswith("python.exe") and not target_exe.lower().endswith("pythonw.exe"):
        return f'"{target_exe}" "%1"'
    main_py = get_main_script_path()
    return f'"{target_exe}" "{main_py}" "%1"'


def is_registered() -> bool:
    """Checks if PrincePDF is registered in HKCU."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROGID}\shell\open\command") as key:
            val, _ = winreg.QueryValueEx(key, "")
            return bool(val)
    except Exception:
        return False


def register_windows_file_association() -> Tuple[bool, str]:
    """
    Registers PrincePDF in HKCU for .pdf files so Windows 11 lists it:
    1. In Windows 11 Default Apps settings
    2. In Right-Click -> 'Open with' menu
    3. In 'How do you want to open this file?' dialog
    """
    try:
        cmd = get_open_command()
        ico = get_icon_path()

        # 1. Register ProgID
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROGID}") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "PDF Document")
            winreg.SetValueEx(key, "FriendlyTypeName", 0, winreg.REG_SZ, "PrincePDF Document")
            if ico:
                winreg.SetValueEx(key, "DefaultIcon", 0, winreg.REG_SZ, f'"{ico}",0')

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROGID}\shell\open\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, cmd)

        # 2. Add to .pdf OpenWithProgids
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.pdf\OpenWithProgids") as key:
            winreg.SetValueEx(key, PROGID, 0, winreg.REG_NONE, b"")

        # 3. Register Application under Software\Classes\Applications\PrincePDF
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\Applications\PrincePDF.exe\shell\open\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, cmd)

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\Applications\PrincePDF.exe\SupportedTypes") as key:
            winreg.SetValueEx(key, ".pdf", 0, winreg.REG_SZ, "")

        # 4. Register Capabilities for Windows Default Apps Settings
        cap_path = rf"Software\{APP_NAME}\Capabilities"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cap_path) as key:
            winreg.SetValueEx(key, "ApplicationDescription", 0, winreg.REG_SZ, APP_DESC)
            winreg.SetValueEx(key, "ApplicationName", 0, winreg.REG_SZ, APP_NAME)

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{cap_path}\FileAssociations") as key:
            winreg.SetValueEx(key, ".pdf", 0, winreg.REG_SZ, PROGID)

        # 5. Register in RegisteredApplications
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\RegisteredApplications") as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cap_path)

        # 6. Notify Windows Shell of association change
        try:
            import ctypes
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None) # SHCNE_ASSOCCHANGED
        except Exception:
            pass

        return True, "Successfully registered PrincePDF in Windows 11."
    except Exception as e:
        return False, f"Registration failed: {e}"


def open_windows_default_apps():
    """Opens Windows 11 Settings to Default Apps page."""
    try:
        # Windows 11 Default Apps URI
        os.startfile("ms-settings:defaultapps")
        return True
    except Exception as e:
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "ms-settings:defaultapps"], shell=True)
            return True
        except Exception:
            return False


def open_windows_open_with(filepath: str):
    """Triggers the native Windows 'Open with' dialog for setting default app."""
    if not filepath or not os.path.exists(filepath):
        return False
    try:
        # rundll32 shell32.dll,OpenAs_RunDLL <file>
        abs_path = os.path.abspath(filepath)
        subprocess.Popen(f'rundll32.exe shell32.dll,OpenAs_RunDLL "{abs_path}"', shell=True)
        return True
    except Exception:
        return False


def create_desktop_shortcut() -> Tuple[bool, str]:
    """Creates a Windows shortcut on the user's Desktop."""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, "PrincePDF.lnk")
        target_exe = get_executable_path()
        ico = get_icon_path()

        if target_exe.lower().endswith("princepdf.exe"):
            target_path = target_exe
            args_str = ""
            work_dir = os.path.dirname(target_exe)
            icon_loc = f'"{target_exe}",0'
        else:
            target_path = get_pythonw_path()
            main_py = get_main_script_path()
            args_str = f'"{main_py}"'
            work_dir = os.path.dirname(main_py)
            icon_loc = f'"{ico}",0' if ico else f'"{target_path}",0'

        # Create shortcut using Windows Script Host (WScript.Shell) via PowerShell
        ps_cmd = (
            f'$WshShell = New-Object -comObject WScript.Shell; '
            f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); '
            f'$Shortcut.TargetPath = "{target_path}"; '
            f'$Shortcut.Arguments = \'{args_str}\'; '
            f'$Shortcut.WorkingDirectory = "{work_dir}"; '
            f'$Shortcut.Description = "{APP_DESC}"; '
            f'$Shortcut.IconLocation = \'{icon_loc}\'; '
            f'$Shortcut.Save()'
        )
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        if res.returncode == 0:
            return True, f"Created shortcut: {shortcut_path}"
        else:
            return False, res.stderr
    except Exception as e:
        return False, str(e)
