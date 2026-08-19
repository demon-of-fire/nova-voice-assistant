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
    excluded_modules = [
        "cv2",
        "fsspec",
        "keras",
        "matplotlib",
        "numba",
        "numpy.distutils",
        "pandas",
        "pygame",
        "pyttsx3",
        "scipy",
        "sklearn",
        "tensorflow",
        "timm",
        "torch",
        "torchaudio",
        "torchvision",
        "transformers",
        "whisper",
    ]

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
        # edge_tts needs its data files
        "--collect-data", "edge_tts",
        "--hidden-import", "comtypes.stream",
        "--hidden-import", "comtypes.client",
        "--hidden-import", "comtypes.gen",
        "--hidden-import", "assistant.platform_integration",
        "--hidden-import", "assistant.windows_integration",
        "--hidden-import", "google.genai",
        "--hidden-import", "google.genai.types",
        "--hidden-import", "pycaw.pycaw",
        "--hidden-import", "screen_brightness_control",
        "--hidden-import", "pystray._win32",
        "--hidden-import", "clr",
        "--hidden-import", "pythonnet",
        "--hidden-import", "clr_loader",
        "--hidden-import", "webview",
        "--hidden-import", "webview.platforms.edgechromium",
        "--hidden-import", "webview.platforms.winforms",
        "--hidden-import", "bottle",
        "--hidden-import", "edge_tts",
        "--hidden-import", "edge_tts.subcoder",
        "--collect-all", "pythonnet",
        "--collect-all", "clr_loader",
        "main.py",
    ]
    for module in excluded_modules:
        cmd.extend(["--exclude-module", module])

    # Add icon if it exists
    if os.path.exists("icon.ico"):
        cmd.extend(["--icon", "icon.ico"])

    print("Building Nova Setup.exe...")
    subprocess.run(cmd, check=True)

    exe_path = os.path.join(dist_dir, "Nova Setup.exe")
    print()
    print("=" * 50)
    print(f"  Done! Nova Setup.exe is at:")
    print(f"  {exe_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
