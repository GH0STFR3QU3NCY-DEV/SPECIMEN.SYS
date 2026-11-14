# Publication plan

**Stage:** Release candidate, not publicly published by this package alone.

## 1. Security gate

- Import only the files from this sanitized public directory. Never push a prior development ZIP, private integration patch, local build cache, personal absolute path, signing key or authentication token.
- Run `python scripts/check_public.py` before each commit. Review any flagged item; a scanner cannot prove that a repository is anonymous or secret-free.
- Audit the **existing remote repository's entire history** before making it public. Removing files in a new commit does not delete them from Git history or existing forks.
- Protect main with CI checks; enable secret scanning and push protection. Default `GITHUB_TOKEN` should have read access only. Never add a personal access token to workflow files.
- Avoid posting the source archive from the development environment. All public builds should derive from the clean repository state.

## 2. GitHub preparation

- Short description: `Standalone CRT-inspired pixel-art biological observation widget for Windows.`
- Suggested topics: `desktop-widget`, `python`, `pyside6`, `pixel-art`, `windows`, `crt`, `retro-computing`, `open-source`, `system-tray`, `sci-fi`.
- Use `docs/images/github-header.png` in the README.
- Upload `docs/images/social-preview.png` in **Settings → Social preview** (1280×640, under 1 MB). GitHub requires this settings action separately from a commit.
- Add screenshots and animated demos from `docs/images`. Do not upload user desktop screenshots (taskbar names, wallpapers, paths or notifications can identify the author).

## 3. Windows release

- Run tests on Windows and manually verify the tray-only window, click-through recovery, right-click menu, splash time, About frame, display mode switching, every size, multi-monitor recovery, and startup preference.
- Push a release-candidate tag `v1.6.0-rc1` after CI passes. The release workflow builds the executable on a Windows hosted runner and uploads a review artifact with SHA-256 checksums. **It does not automatically create a public release.** Inspect the compiled binary and run a visible Windows test before manually publishing a prerelease.
- If possible, sign published executables using a consistent Authenticode certificate. An unsigned or new Windows application can trigger SmartScreen, and users should be given transparent risk information.
- Do not label the GitHub release `stable` until a real Windows smoke test has been documented.

## 4. Exposure plan

1. Share a short 10–15 second visual demo with the title `I made a tiny CRT-style sci-fi desktop widget for Windows`.
2. Link the project only where community rules permit self-promotion. Start with a relevant side-project or desktop-customization community, avoiding a copy-pasted cross-post campaign.
3. Lead with the animated preview and standalone behaviour, not the build stack. In the comments, explain source availability, RAM/CPU use (once measured), and safe installation.
4. Publish an issue template for bug reports and keep the README screenshots current.
5. Collect feedback on display legibility, transparent edges, tray recovery and accessibility, then issue a verified v1.6.0 stable release.

## Privacy limitations

A GitHub repository reveals its hosting account, commit metadata, public workflow logs and release publisher. This package does not embed personal information, but it cannot make the account operating the repository anonymous. If personal separation is essential, publish from a separately controlled project identity before any public pushes. Every existing commit must be considered.

## IP/branding limitation

This is a science-fiction fan-style artwork. It includes some recognizable fictional design motifs; publishing does not establish intellectual-property rights to third-party designs. See ASSETS.md and consult the relevant rights policy before commercial distribution.
