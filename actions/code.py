"""Code execution: run Python code, create script files."""

import subprocess
import os
import sys
import shutil
from actions.confirmation import ask_confirmation


def _python_interp():
    """Find a real Python interpreter. In a frozen (PyInstaller) build
    sys.executable points at Nova.exe, which can't run `-c` code."""
    if not getattr(sys, "frozen", False):
        return sys.executable
    for cand in ("pythonw", "python", "py"):
        p = shutil.which(cand)
        if p:
            return p
    return sys.executable


def run_python(code):
    """Execute Python code and return the output."""
    if not ask_confirmation(f"Run Python code:\n{code[:300]}"):
        return "Action cancelled by user."

    try:
        result = subprocess.run(
            [_python_interp(), "-c", code],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip()
        errors = result.stderr.strip()

        if errors and not output:
            return f"Error:\n{errors[:2000]}"
        if errors and output:
            return f"{output[:1500]}\n\nWarnings:\n{errors[:500]}"
        if output:
            if len(output) > 2000:
                output = output[:2000] + "\n... (truncated)"
            return output
        return "(code ran successfully with no output)"
    except subprocess.TimeoutExpired:
        return "Code execution timed out after 30 seconds."
    except Exception as e:
        return f"Error running Python code: {e}"


def create_script(path, code, language="python"):
    """Create a script file with the given code."""
    full = os.path.expandvars(os.path.expanduser(path))
    if not ask_confirmation(f"Create {language} script:\n{full}"):
        return "Action cancelled by user."

    try:
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            # Add shebang for common languages
            if language.lower() == "python" and not code.startswith("#!"):
                f.write("#!/usr/bin/env python3\n")
            elif language.lower() in ("bash", "sh") and not code.startswith("#!"):
                f.write("#!/bin/bash\n")
            f.write(code)
        return f"Created {language} script at {full}."
    except Exception as e:
        return f"Error creating script: {e}"
