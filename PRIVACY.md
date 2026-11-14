# Privacy

SPECIMEN.SYS is a local-only desktop application. It does not send analytics, diagnostics or user data to a service. It does not ask for credentials, require an account, or use background network requests.

Settings (size, display style, window position, animation options, and other preferences) are stored locally using Qt `QSettings` under an application-specific namespace. Persistent diagnostic logging is disabled by default. When explicitly enabled with `SPECIMEN_DEBUG_LOGS=1`, error logs are stored locally beneath `%LOCALAPPDATA%\SpecimenSys\logs` on Windows; such logs may contain local paths and should never be posted publicly without manual redaction. Windows startup registration, if enabled manually, is limited to the current user's `Run` registry key and can be disabled from Preferences.

The repository's GitHub Actions only run during development and releases. They are not part of the installed program. Windows and third-party package managers may have their own telemetry or update mechanisms unrelated to this application.
