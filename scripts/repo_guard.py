"""Repository guard for the public SPECIMEN.SYS repository.

Fails when anything in the checked-out repository:
  * was authored, committed or tagged by an identity that isn't on the allowlist
    (both the name and the email are checked),
  * carries a co-author or session trailer (commit or tag message),
  * contains a blocked word: in a file path, file text, text embedded in a binary
    file (ASCII and UTF-16), a commit message, or an annotated tag.

Blocked words and allowed identities are stored only as salted SHA-256 hashes, so
this file does not disclose what it looks for. Run with full history:
`python scripts/repo_guard.py`.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

SALT = "specimen-guard:"
ID_SALT = "specimen-guard-id:"
BLOCKED_FILE = Path(__file__).with_name("repo_guard_hashes.txt")

# Salted SHA-256 of the allowed emails and names: the owner, Dependabot and GitHub's own merges.
ALLOWED_EMAILS = {
    "d3b7bb17376fa97e806cf9e137b3ce26017d3e27f8411e0432d3b8d5f7ae224e",
    "e96cfb5f3a34884ea7e98c766affacf2ed07562065ce1ecf4d7cc6e3c0d5c84c",
    "7f8abbce52462a7c2de555d2f757bf51b086217b95867eabe758c984f4dafffd",
}
ALLOWED_NAMES = {
    "ecd4ea362b3e05c8188d5cb2ac0ad35b854ba0ebe3a55b88d0642bbaa0e01818",
    "b3bc791c7d8ea7349bd67ef8b71f174ab2307e9d88692d70149338f2489a24c6",
    "a84cf939966c414dafb1da12f2339e526473b28007c1aca6fe9afaa3c7c37a85",
}

TRAILER = re.compile(r"^\s*[\w-]*(co-authored-by|session)\s*:", re.I | re.M)
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.\-]*")
ASCII_RUN = re.compile(rb"[\x20-\x7e]{4,}")
UTF16_RUN = re.compile(rb"(?:[\x20-\x7e]\x00){4,}")


def _id_hash(value: str) -> str:
    return hashlib.sha256((ID_SALT + value.strip().lower()).encode()).hexdigest()


def blocked_hashes() -> set[str]:
    return {line.strip().lower() for line in BLOCKED_FILE.read_text(encoding="utf-8").split() if line.strip()}


def words(text: str):
    for token in TOKEN.findall(text):
        token = token.strip("._-")
        if not token:
            continue
        yield token.lower()
        for part in re.split(r"[._\-]+", token):
            if not part:
                continue
            yield part.lower()
            # camelCase / PascalCase / digit boundaries: FooBar2 -> foo, bar, 2
            for piece in re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", part):
                yield piece.lower()


# Further blocked words can be supplied privately (an Actions secret or a local file outside the repo):
# GUARD_PRIVATE_SALT and GUARD_PRIVATE_HASHES (whitespace-separated SHA-256 of salt + word).
PRIVATE_SALT = os.environ.get("GUARD_PRIVATE_SALT", "")
PRIVATE_HASHES = {h.lower() for h in os.environ.get("GUARD_PRIVATE_HASHES", "").split()}


def hits(text: str, hashes: set[str]) -> bool:
    for w in words(text):
        if hashlib.sha256((SALT + w).encode()).hexdigest() in hashes:
            return True
        if PRIVATE_SALT and hashlib.sha256((PRIVATE_SALT + w).encode()).hexdigest() in PRIVATE_HASHES:
            return True
    return False


def binary_text(data: bytes) -> str:
    runs = [m.group().decode("ascii") for m in ASCII_RUN.finditer(data)]
    runs += [m.group().decode("utf-16-le") for m in UTF16_RUN.finditer(data)]
    return "\n".join(runs)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def check_identity(label: str, name: str, email: str, problems: list[str]) -> None:
    if _id_hash(email) not in ALLOWED_EMAILS or _id_hash(name) not in ALLOWED_NAMES:
        problems.append(f"{label}: identity not on the allowlist")


def main() -> int:
    hashes = blocked_hashes()
    problems: list[str] = []
    if not PRIVATE_SALT:
        if os.environ.get("GUARD_REQUIRE_PRIVATE", "").lower() == "true":
            print("Repository guard: FAIL\n  private word list required here but not supplied")
            return 1
        print("Repository guard: note: private word list not supplied; public list only")

    log = git("log", "--all", "--format=%H%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%B%x1e")
    for entry in filter(None, (e.strip() for e in log.split("\x1e"))):
        sha, an, ae, cn, ce, message = (entry.split("\x1f") + [""] * 6)[:6]
        short = sha[:9]
        check_identity(short, an, ae, problems)
        check_identity(short, cn, ce, problems)
        if TRAILER.search(message):
            problems.append(f"{short}: commit message has a co-author or session trailer")
        if hits(message, hashes):
            problems.append(f"{short}: commit message contains a blocked word")

    tags = git("for-each-ref", "refs/tags",
               "--format=%(refname:short)%1f%(objecttype)%1f%(taggername)%1f%(taggeremail:trim)%1f%(contents)%1e")
    for entry in filter(None, (e.strip() for e in tags.split("\x1e"))):
        ref, kind, tn, te, message = (entry.split("\x1f") + [""] * 5)[:5]
        label = f"tag {ref}"
        if hits(ref, hashes):
            problems.append(f"{label}: tag name contains a blocked word")
        if kind != "tag":
            continue  # lightweight tag: points at a commit already checked above
        check_identity(label, tn, te, problems)
        if TRAILER.search(message):
            problems.append(f"{label}: tag message has a co-author or session trailer")
        if hits(message, hashes):
            problems.append(f"{label}: tag message contains a blocked word")

    for path in git("ls-files").splitlines():
        if hits(path, hashes):
            problems.append(f"{path}: path contains a blocked word")
            continue
        p = Path(path)
        if not p.is_file():
            continue
        data = p.read_bytes()
        if b"\0" in data[:8192]:
            text, kind = binary_text(data), "text embedded in a binary file"
        else:
            text, kind = data.decode("utf-8", "replace"), "file text"
        if hits(text, hashes):
            problems.append(f"{path}: {kind} contains a blocked word")

    if problems:
        print("Repository guard: FAIL")
        for line in sorted(set(problems)):
            print("  " + line)
        return 1
    print("Repository guard: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
