# Release checklist

- [ ] GitHub repository clone and full **existing history** inspected
- [ ] No private integration, credentials, usernames, personal paths, project identifiers or private screenshots
- [ ] Source scan `python scripts/check_public.py` passes
- [ ] Unit tests pass on local runtime and Windows CI
- [ ] Windows PyInstaller `.exe` launched and confirmed **tray-only**
- [ ] Silent splash displayed for ~2 seconds
- [ ] Borderless About opens and closes with Escape/click, no audio
- [ ] Classic and Detailed styles both animate correctly
- [ ] Compact (449×561), Standard, Large verified on Windows
- [ ] CRT roll toggle, transparency and GPU/CPU consumption inspected
- [ ] Click-through cannot strand the window
- [ ] No startup registry entry until explicitly enabled
- [ ] Screenshots inspected for author information or private branding
- [ ] Executable malware scan / SmartScreen expectations documented
- [ ] Public artwork and licensing situation reviewed
- [ ] GitHub Social preview uploaded (repository setting, not automatically by git)
- [ ] Repository release marked `pre-release` until Windows validation complete

- [ ] Verify the 2-second frameless boot plate and click-to-close About plaque on a visible Windows desktop.
- [ ] Check the startup/status bar progresses naturally without flicker on high DPI and multiple monitors.
- [ ] Confirm the About plaque never appears as a taskbar window and stays silent.

## Privacy publication blocker

- [ ] Review GitHub account/profile identity and commit authorship before upload
- [ ] Audit entire Git history and branches, not only current files
- [ ] Build downloadable executable on a clean hosted runner, not a personal PC
- [ ] Check produced EXE and ZIP for private strings, debug paths, credentials and user data
- [ ] Ensure no local publisher, publishing logs or VCS internals are in the source archive
- [ ] Confirm image and animation files have no EXIF/XMP/text author metadata
- [ ] Do not share real desktop screenshots or unredacted issue logs on social media
