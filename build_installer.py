"""Build pipeline: PyInstaller -> Nova.exe -> embed in C# installer -> compile setup.exe"""

import subprocess
import sys
import os
import shutil
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALLER_DIR = os.path.join(PROJECT_DIR, "installer")
NOVA_EXE = os.path.join(PROJECT_DIR, "Nova.exe")
SETUP_EXE = os.path.join(PROJECT_DIR, "setup.exe")
CSHARP_SRC = os.path.join(INSTALLER_DIR, "installer.cs")
RESOURCE_FILE = os.path.join(INSTALLER_DIR, "Nova.exe")


def step(msg):
    print(f"\n{'=' * 60}")
    print(f"  {msg}")
    print(f"{'=' * 60}")


def find_csc():
    """Find the C# compiler (csc.exe)."""
    windir = os.environ.get("WINDIR", "C:\\Windows")
    candidates = [
        os.path.join(windir, "Microsoft.NET", "Framework64", "v4.0.30319", "csc.exe"),
        os.path.join(windir, "Microsoft.NET", "Framework", "v4.0.30319", "csc.exe"),
    ]
    try:
        result = subprocess.run(
            ["where", "csc"],
            capture_output=True, text=True, timeout=5,
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if lines:
            return lines[0]
    except FileNotFoundError:
        pass

    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def kill_nova_processes():
    """Kill any running Nova instances to avoid file-lock issues."""
    try:
        result = subprocess.run(
            ["taskkill", "/f", "/im", "Nova.exe"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            print("  Killed running Nova processes")
            time.sleep(1)
    except Exception:
        pass


def clean_old_build_artifacts():
    """Remove stale build artifacts that can interfere with PyInstaller."""
    spec = os.path.join(PROJECT_DIR, "Nova.spec")
    if os.path.isfile(spec):
        os.remove(spec)
        print("  Removed stale Nova.spec")
    build_dir = os.path.join(PROJECT_DIR, "build")
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)
        print("  Removed stale build/ directory")
    if os.path.isfile(NOVA_EXE):
        os.remove(NOVA_EXE)
        print("  Removed stale Nova.exe")


def build_nova_exe():
    """Run PyInstaller to build Nova.exe."""
    step("Step 1: Building Nova.exe with PyInstaller")

    build_script = os.path.join(PROJECT_DIR, "build.py")
    python = sys.executable

    if os.path.isfile(build_script):
        result = subprocess.run(
            [python, build_script],
            cwd=PROJECT_DIR,
            capture_output=True, text=True, timeout=600,
        )
        out = result.stdout
        err = result.stderr
        if len(out) > 600:
            out = "...\n" + out[-600:]
        if out.strip():
            print(f"  {out.strip()}")
        if err.strip():
            print(f"  Warnings/Errors: {err.strip()[:400]}")
        if result.returncode != 0:
            raise RuntimeError("PyInstaller build failed. See errors above.")
    else:
        excluded = [
            "cv2", "edge_tts", "fsspec", "keras", "matplotlib",
            "numba", "numpy.distutils", "pandas", "pygame", "pyttsx3",
            "scipy", "sklearn", "tensorflow", "timm", "torch",
            "torchaudio", "torchvision", "transformers", "whisper",
        ]
        cmd = [
            python, "-m", "PyInstaller",
            "--noconfirm", "--onefile", "--windowed",
            "--name", "Nova",
            "--distpath", PROJECT_DIR,
            "--add-data", f"config.py{os.pathsep}.",
            "--add-data", f"assistant{os.pathsep}assistant",
            "--add-data", f"actions{os.pathsep}actions",
            "--add-data", f"sounds{os.pathsep}sounds",
            "--add-data", f"nvdaControllerClient64.dll{os.pathsep}.",
            "--add-data", f"Tolk.dll{os.pathsep}.",
            "--hidden-import", "comtypes.stream",
            "--hidden-import", "google.genai",
            "--hidden-import", "google.genai.types",
            "--hidden-import", "pycaw.pycaw",
            "--hidden-import", "screen_brightness_control",
            "--hidden-import", "pystray._win32",
            "--hidden-import", "clr",
            "--hidden-import", "pythonnet",
            "--hidden-import", "clr_loader",
            "--hidden-import", "webview",
            "--hidden-import", "webview.platforms.winforms",
            "--hidden-import", "bottle",
            "--collect-all", "pythonnet",
            "--collect-all", "clr_loader",
            "main.py",
        ]
        for mod in excluded:
            cmd.extend(["--exclude-module", mod])

        print("  Running PyInstaller (this may take several minutes)...")
        result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=600)
        out = result.stdout
        err = result.stderr
        if len(out) > 600:
            out = "...\n" + out[-600:]
        if out.strip():
            print(f"  {out.strip()}")
        if err.strip():
            print(f"  Warnings: {err.strip()[:400]}")
        if result.returncode != 0:
            raise RuntimeError("PyInstaller build failed.")

    if not os.path.isfile(NOVA_EXE):
        raise RuntimeError(f"Nova.exe not found at {NOVA_EXE}")

    size_mb = os.path.getsize(NOVA_EXE) / (1024 * 1024)
    print(f"  Nova.exe built: {size_mb:.1f} MB")


def embed_in_installer():
    """Copy Nova.exe into installer directory and compile setup.exe."""
    step("Step 2: Embedding Nova.exe in C# installer")

    resource_path = os.path.join(INSTALLER_DIR, "Nova.exe")
    shutil.copy2(NOVA_EXE, resource_path)
    print(f"  Copied Nova.exe ({os.path.getsize(resource_path) / (1024*1024):.1f} MB)")

    step("Step 3: Compiling setup.exe with csc.exe")

    csc_path = find_csc()
    if not csc_path:
        print("  ERROR: Could not find C# compiler (csc.exe).")
        print("  Install .NET Framework SDK or Visual Studio Build Tools.")
        print("  Download: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022")
        raise RuntimeError("C# compiler not found")

    print(f"  Using compiler: {csc_path}")

    cmd = [
        csc_path,
        "/nologo",
        "/target:winexe",
        "/reference:System.Windows.Forms.dll",
        "/reference:System.Drawing.dll",
        f"/resource:{resource_path},Nova.exe",
        f"/out:{SETUP_EXE}",
        CSHARP_SRC,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")
    if result.stderr.strip():
        print(f"  Compiler messages: {result.stderr.strip()}")
    if result.returncode != 0:
        raise RuntimeError("C# compilation failed")

    if not os.path.isfile(SETUP_EXE):
        raise RuntimeError(f"setup.exe not created at {SETUP_EXE}")

    size_mb = os.path.getsize(SETUP_EXE) / (1024 * 1024)
    print(f"  setup.exe compiled: {size_mb:.1f} MB")


def cleanup():
    """Clean up intermediate files."""
    step("Step 4: Cleaning up")

    # Remove the copy in installer dir
    resource_path = os.path.join(INSTALLER_DIR, "Nova.exe")
    if os.path.isfile(resource_path):
        os.remove(resource_path)
        print("  Removed temporary Nova.exe copy from installer/")

    # Remove spec and build dirs if they exist
    spec_file = os.path.join(PROJECT_DIR, "Nova.spec")
    if os.path.isfile(spec_file):
        os.remove(spec_file)
        print("  Removed Nova.spec")

    build_dir = os.path.join(PROJECT_DIR, "build")
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)
        print("  Removed build/ directory")

    # Remove the intermediate Nova.exe
    if os.path.isfile(NOVA_EXE):
        os.remove(NOVA_EXE)
        print("  Removed intermediate Nova.exe")

    print("\n  Done!")


def main():
    print()
    print("  +================================================+")
    print("  |     Nova Voice Assistant - Installer Build     |")
    print("  +================================================+")

    # Pre-flight checks
    if not os.path.isfile(CSHARP_SRC):
        print(f"  ERROR: C# source not found at {CSHARP_SRC}")
        sys.exit(1)
    if not os.path.isfile(os.path.join(PROJECT_DIR, "main.py")):
        print(f"  ERROR: main.py not found in project directory")
        sys.exit(1)

    csc = find_csc()
    if not csc:
        print("  WARNING: Could not find C# compiler (csc.exe).")
        print("  The installer step will fail. Install .NET Framework SDK first.")
        print("  However, we'll still build Nova.exe for you.\n")

    try:
        kill_nova_processes()
        clean_old_build_artifacts()
        build_nova_exe()

        if csc:
            embed_in_installer()
            cleanup()

            print()
            print("=" * 60)
            print(f"  SUCCESS! setup.exe created at:")
            print(f"  {SETUP_EXE}")
            print(f"  Size: {os.path.getsize(SETUP_EXE) / (1024*1024):.1f} MB")
            print("=" * 60)
            print()
            print("  To distribute:")
            print(f"  1. Share 'setup.exe' with users")
            print("  2. They run it and click Install")
            print("  3. Nova.exe is extracted to %LOCALAPPDATA%\\Nova\\")
            print()
        else:
            print()
            print("=" * 60)
            print(f"  PARTIAL SUCCESS! Nova.exe built at:")
            print(f"  {NOVA_EXE}")
            print(f"  Size: {os.path.getsize(NOVA_EXE) / (1024*1024):.1f} MB")
            print("=" * 60)
            print()
            print("  To build the installer manually, install .NET Framework")
            print("  Build Tools from: https://visualstudio.microsoft.com/")
            print("  downloads/#build-tools-for-visual-studio-2022")
            print()

    except Exception as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
