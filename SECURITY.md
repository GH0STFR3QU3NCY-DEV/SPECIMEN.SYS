# Security policy

## Supported versions

The current release candidate is `1.6.1-rc2` (source review only; no verified Windows binary). Older builds are unsupported.

## Reporting vulnerabilities

Please use the repository's **Security → Report a vulnerability** option where available, rather than publishing exploitation details in a public issue. Do not submit credentials, system paths, crash dumps containing personal data, or private source files to public Issues.

## Runtime boundaries

The application is an offline PySide6 desktop widget. It loads bundled image files, stores local preferences, optionally registers per-user startup, and optionally logs errors. It should never ask for administrator rights, execute downloaded scripts, or contact external domains at runtime.

## Release process

- A public-disclosure scanner runs before every build.
- CI uses read-only GitHub token permissions.
- Tagged builds are separated from untrusted pull-request checks and produce review artifacts; no executable is released automatically.
- Builds are unsigned unless an explicit signing process is added. No claim of malware-free status or Windows SmartScreen reputation is implied.

File release integrity should be verified against the published SHA-256 manifest.

## Publication privacy gate

This source tree must be checked before publishing. Do not commit your local Git
configuration, ZIPs from development projects, screen captures of your desktop,
or locally compiled binaries. A Windows EXE must be built on a clean CI runner,
then reviewed separately for embedded paths and metadata. Public GitHub account
ownership, commit attribution, and server-side logs are separate from the source
package and cannot be made anonymous by removing file metadata.
