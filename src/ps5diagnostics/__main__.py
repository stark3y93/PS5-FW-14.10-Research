"""Windows desktop view of approved, locally recorded console observations.

The dashboard reads only the local SQLite database. It never opens a socket or
contacts a console. Future observations require a separately approved procedure.
"""
from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

REMOTE_PLAY_URL = "https://www.playstation.com/en-gb/support/games/playstation-remote-play-on-pc-and-mac/"
VERSION_URL = "https://www.playstation.com/en-ca/support/hardware/playstation-system-software-application-version/"


def dashboard_data(database: Path) -> dict:
    observations: list[dict] = []
    if database.exists():
        with closing(sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True)) as con:
            con.row_factory = sqlite3.Row
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='console_observation'").fetchone():
                observations = [dict(row) for row in con.execute(
                    "SELECT observed_utc, console_label, category, value, verification, method, source_url "
                    "FROM console_observation ORDER BY observed_utc DESC, id DESC LIMIT 50"
                )]
    version_rows = [row for row in observations if row["category"] == "firmware_version" and row["verification"] == "console-reported"]
    connection_rows = [row for row in observations if row["category"] == "connection_status" and row["verification"] == "console-reported"]
    return {
        "connection": connection_rows[0]["value"] if connection_rows else "Not observed — no console contact authorised",
        "firmware": version_rows[0]["value"] if version_rows else "Unknown — 14.10 is a research target, not a console reading",
        "services": [
            ("PS Remote Play", "Documented by Sony; availability on this console unverified", REMOTE_PLAY_URL),
            ("Console Information", "Documented on-device version display; console availability unverified", VERSION_URL),
        ],
        "observations": observations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline Windows PS5 diagnostics dashboard")
    parser.add_argument("--database", type=Path, default=Path("research/knowledge-base/ps5-research.sqlite3"))
    args = parser.parse_args()
    data = dashboard_data(args.database)
    import tkinter as tk
    from tkinter import ttk

    window = tk.Tk()
    window.title("PS5 Connection & Diagnostics — offline preparation")
    window.geometry("900x600")
    frame = ttk.Frame(window, padding=18)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="PS5 Connection & Diagnostics", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Preparation only. This app reads local research data and never contacts the console.").pack(anchor="w", pady=(0, 14))
    ttk.Label(frame, text=f"Connection status: {data['connection']}", font=("Segoe UI", 11, "bold")).pack(anchor="w")
    ttk.Label(frame, text=f"Console-reported firmware: {data['firmware']}").pack(anchor="w", pady=(2, 16))
    ttk.Label(frame, text="Documented methods (console availability unverified)", font=("Segoe UI", 11, "bold")).pack(anchor="w")
    for name, status, url in data["services"]:
        ttk.Label(frame, text=f"• {name}: {status}").pack(anchor="w")
        ttk.Label(frame, text=url, foreground="#285a9f").pack(anchor="w", padx=16)
    ttk.Label(frame, text="Approved observations", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(18, 4))
    columns = ("time", "label", "category", "value", "verification", "method")
    table = ttk.Treeview(frame, columns=columns, show="headings", height=10)
    for column in columns:
        table.heading(column, text=column.replace("_", " ").title())
        table.column(column, width=130 if column != "value" else 220)
    for row in data["observations"]:
        table.insert("", "end", values=tuple(row[key] for key in ("observed_utc", "console_label", "category", "value", "verification", "method")))
    table.pack(fill="both", expand=True)
    window.mainloop()


if __name__ == "__main__":
    main()
