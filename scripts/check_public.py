"""Release-stage privacy and source-integrity checks.

Generic checks only. A separate, unpublished reviewer may use a private denylist.
This program is not a guarantee of anonymity, complete secret removal,
or safety of the hosting account, commit history or compiled executable.
"""
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = {'.py', '.pyw', '.md', '.txt', '.cmd', '.ps1', '.json', '.yaml', '.yml',
        '.toml', '.ini', '.html', '.sh', '.cfg', '.gitignore'}
MEDIA = {'.png', '.webp', '.ico'}
ALLOWED_SUFFIXES = TEXT | MEDIA | {''}
ALLOWED_ROOT = {'.github', '.gitignore', 'ASSETS.md', 'BUILD-EXE.cmd',
                'CHANGELOG.md', 'CONTRIBUTING.md', 'INSTALL.cmd', 'LICENSE',
                'PRIVACY.md', 'README.md', 'RELEASE-CHECKLIST.md',
                'RUN-DEBUG.cmd', 'RUN-SPECIMEN.cmd', 'SECURITY.md',
                'branding', 'docs', 'requirements.txt', 'scripts',
                'specimen.py', 'specimen.pyw', 'specimen_sys', 'tests'}
BAD_COMPONENTS = {'.git', '.venv', '__pycache__', '.pytest_cache', 'build',
                  'dist', 'userdata', 'local_data', '.vscode', '.idea',
                  'node_modules'}
BAD_NAMES = {'desktop.ini', 'thumbs.db', '.ds_store', '.env', 'settings.ini',
             'publish.py', 'publish.cmd', 'publish-log.txt'}
BAD_SUFFIXES = {'.exe', '.dll', '.pdb', '.pyc', '.pyo', '.pyd', '.msi', '.log',
                '.pem', '.pfx', '.p12', '.key', '.token', '.sqlite', '.db'}
PATTERNS = {
    'email address': re.compile(r'(?i)\b[A-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b'),
    'Windows user directory': re.compile(r'(?i)\b[A-Z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\s"\']+'),
    'Unix user directory': re.compile(r'(?i)(?:/home|/Users)/[A-Za-z0-9_.-]+/(?:Desktop|Documents|Downloads|projects|workspace)(?:/|\b)'),
    'UNC machine share': re.compile(r'(?i)\\\\[A-Za-z0-9_.-]+\\[A-Za-z0-9$_.-]+\\'),
    'specific GitHub repository': re.compile(r'(?i)https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+'),
    'credential assignment': re.compile(r'(?i)\b(?:api[_-]?key|auth[_-]?token|client[_-]?secret|password|access[_-]?token)\s*[:=]\s*["\']?[A-Za-z0-9+/=_-]{18,}'),
    'known credential format': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)'),
}


def _png_metadata(path: Path):
    data = path.read_bytes()
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        return ['invalid PNG signature']
    pos, issues = 8, []
    while pos + 12 <= len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        kind = data[pos+4:pos+8]
        if length > len(data) - pos - 12:
            return issues + ['invalid PNG chunk length']
        if kind in {b'tEXt', b'iTXt', b'zTXt', b'eXIf', b'iCCP'}:
            issues.append('embedded PNG metadata chunk: ' + kind.decode('ascii'))
        pos += 12 + length
        if kind == b'IEND':
            if pos != len(data): issues.append('PNG data appended after IEND')
            break
    return issues


def _webp_metadata(path: Path):
    data = path.read_bytes()
    if data[:4] != b'RIFF' or data[8:12] != b'WEBP':
        return ['invalid WebP signature']
    pos, issues = 12, []
    while pos + 8 <= len(data):
        kind = data[pos:pos+4]
        length = struct.unpack('<I', data[pos+4:pos+8])[0]
        if kind in {b'EXIF', b'XMP ', b'ICCP'}:
            issues.append('embedded WebP metadata chunk: ' + kind.decode('ascii'))
        if length > len(data) - pos - 8:
            return issues + ['invalid WebP chunk length']
        pos += 8 + length + (length % 2)
    return issues


def audit():
    problems = []
    for p in sorted(ROOT.rglob('*')):
        rel = p.relative_to(ROOT)
        parts = [v.lower() for v in rel.parts]
        label = rel.as_posix()
        if p.is_symlink():
            problems.append(f'symlink prohibited: {label}')
            continue
        # GitHub Actions checkout creates local Git bookkeeping. It is not
        # tracked source and cannot be included in the published package.
        # Keep rejecting every other unexpected top-level entry.
        if parts[0] == '.git':
            continue
        if parts[0] not in {x.lower() for x in ALLOWED_ROOT}:
            problems.append(f'unknown root entry: {label}')
        if any(v in BAD_COMPONENTS for v in parts):
            # Local Python/build caches are ignored by Git and not release source.
            # The separate archive audit rejects these if a ZIP contains them.
            continue
        if p.name.lower() in BAD_NAMES or p.suffix.lower() in BAD_SUFFIXES:
            problems.append(f'unapproved file: {label}')
        if not p.is_file():
            continue
        if p.suffix.lower() not in ALLOWED_SUFFIXES:
            problems.append(f'unrecognised file type: {label}')
        if p.stat().st_size > 50 * 1024 * 1024:
            problems.append(f'oversize file: {label}')
        if p.suffix.lower() == '.png':
            problems += [f'{label}: {issue}' for issue in _png_metadata(p)]
        elif p.suffix.lower() == '.webp':
            problems += [f'{label}: {issue}' for issue in _webp_metadata(p)]
        elif p.suffix.lower() in TEXT or p.name == 'LICENSE':
            try:
                content = p.read_text('utf-8')
            except UnicodeError:
                problems.append(f'non-UTF-8 source: {label}')
                continue
            # Pattern source is generic source code, not a credential or user path.
            if p.name == 'check_public.py':
                continue
            for description, pattern in PATTERNS.items():
                if pattern.search(content):
                    problems.append(f'{label}: possible {description}')
    return sorted(set(problems))


if __name__ == '__main__':
    failures = audit()
    if failures:
        print('PUBLICATION BLOCKED:')
        for failure in failures: print(' - ' + failure)
        sys.exit(1)
    print('Public package static privacy scan: PASS; attribution/history/build checks are separate.')
