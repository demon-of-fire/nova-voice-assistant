"""Build Nova into a standalone .exe using PyInstaller."""

import subprocess
import sys
import os

def main():
    # Install pyinstaller if not present
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Output directly into the project folder
    project_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = project_dir  # put Nova.exe right in the main folder

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",                    # no console window
        "--name", "Nova",
        "--distpath", dist_dir,
        "--add-data", f"config.py{os.pathsep}.",
        "--add-data", f"assistant{os.pathsep}assistant",
        "--add-data", f"actions{os.pathsep}actions",
        "--add-data", f"sounds{os.pathsep}sounds",
        "--add-data", f"nvdaControllerClient64.dll{os.pathsep}.",
        "--add-data", f"Tolk.dll{os.pathsep}.",
        "--hidden-import", "pyttsx3.drivers",
        "--hidden-import", "pyttsx3.drivers.sapi5",
        "--hidden-import", "comtypes.stream",
        "--hidden-import", "google.genai",
        "--hidden-import", "google.genai.types",
        "--hidden-import", "pycaw.pycaw",
        "--hidden-import", "screen_brightness_control",
        "--hidden-import", "pystray._win32",
        "--hidden-import", "pygame",
        "--hidden-import", "pygame.mixer",
        "--hidden-import", "edge_tts",
        "main.py",
    ]

    # Add icon if it exists
    if os.path.exists("icon.ico"):
        cmd.extend(["--icon", "icon.ico"])

    print("Building Nova.exe...")
    subprocess.run(cmd, check=True)

    exe_path = os.path.join(dist_dir, "Nova.exe")
    print()
    print("=" * 50)
    print(f"  Done! Nova.exe is at:")
    print(f"  {exe_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
