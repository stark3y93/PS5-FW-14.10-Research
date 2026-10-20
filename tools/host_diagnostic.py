#!/usr/bin/env python3
"""Run the restricted diagnostic host directly, without installation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ps5fwlab.diagnostic_host import main

if __name__ == "__main__":
    raise SystemExit(main())
