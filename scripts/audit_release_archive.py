"""Inspect CI-produced SPECIMEN.SYS ZIP before a public prerelease.

A structural and generic-identifier check; not an antivirus verdict or
proof that a public hosting account is anonymous.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/audit_release_archive.py ARCHIVE.zip")
        return 2
    archive = Path(sys.argv[1])
    if not archive.is_file():
        raise FileNotFoundError(archive)
    errors = []
    forbidden_parts = {".git", ".venv", "__pycache__", "userdata", "local_data",
                       ".vscode", ".idea", "test-results", ".pytest_cache"}
    forbidden_exts = (".pem", ".key", ".pfx", ".p12", ".env", ".log", ".sqlite", ".db", ".pdb")
    personal_path = re.compile(rb"(?i)(?:[A-Z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\x00\r\n]{2,100}|/home/[a-zA-Z0-9_.-]{2,50}/)")
    credentials = re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
    with zipfile.ZipFile(archive) as z:
        corrupt = z.testzip()
        if corrupt:
            errors.append("Corrupt archive member: " + corrupt)
        members = [i for i in z.infolist() if not i.is_dir()]
        names = {i.filename.replace("\\", "/") for i in members}
        if "SPECIMEN.SYS/SPECIMEN.SYS.exe" not in names:
            errors.append("Missing Windows executable")
        if "SPECIMEN.SYS/_internal/branding/specimen.ico" not in names:
            errors.append("Missing tray/executable icon")
        if not any("/specimen_sys/assets/" in n and n.endswith(".png") for n in names):
            errors.append("Missing bundled animation assets")
        for item in members:
            name = item.filename.replace("\\", "/")
            parts = name.split("/")
            if len(parts) < 2 or parts[0] != "SPECIMEN.SYS" or ".." in parts:
                errors.append("Unexpected archive path: " + name)
            if any(part.lower() in forbidden_parts for part in parts):
                errors.append("Development/private folder in archive: " + name)
            if name.lower().endswith(forbidden_exts):
                errors.append("Private or debug file extension in archive: " + name)
            if item.file_size > 400 * 1024 * 1024:
                errors.append("Oversized member: " + name)
            # Restrict content inspection to application-authored assets and
            # launcher. Third-party runtime DLLs may contain upstream debug paths.
            if name.endswith(".exe") or name.endswith("layer_manifest.json"):
                data = z.read(item)
                if credentials.search(data):
                    errors.append("Credential-shaped data in application file: " + name)
                if personal_path.search(data):
                    errors.append("Local user directory in application file: " + name)
    if errors:
        for e in errors:
            print("BLOCKED:", e)
        return 1
    print(f"Review ZIP structural/identifier scan: PASS ({len(members)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
