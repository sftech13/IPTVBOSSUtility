from cx_Freeze import setup, Executable
import platform

base = "Win32GUI" if platform.system() == "Windows" else None

setup(
    name="IPTV Stream Checker",
    version="1.0",
    description="Check IPTV stream quality from .m3u playlists",
    options={"build_exe": {
        "packages": ["tkinter", "requests", "concurrent", "logging"],
        "include_files": ["iptv_icon.ico", "iptv_icon.png"]
    }},
    executables=[Executable("iptv_gui_full.py", base=base, icon="iptv_icon.ico")]
)
