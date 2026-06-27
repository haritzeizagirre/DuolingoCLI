"""🦉 DuolingoCLI - Practice Duolingo from your terminal."""

import os
import sys

# Force UTF-8 encoding on Windows to support emojis in terminal
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    # Also try to set console to UTF-8
    try:
        os.system("chcp 65001 >nul 2>&1")
    except Exception:
        pass

__version__ = "0.1.0"
