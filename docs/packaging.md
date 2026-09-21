# Packaging

## Windows download (release)

Published builds are attached to [GitHub Releases](https://github.com/LucaVerduyn/local-ai/releases).
Extract the zip and run `LocalAI.exe`. Ollama is still required separately.

## Windows (from source)

```powershell
powershell -File packaging/windows/build.ps1
```

Output: `packaging/windows/dist/LocalAI/LocalAI.exe`

## Linux

```bash
chmod +x packaging/linux/build.sh
bash packaging/linux/build.sh
```

Output: `packaging/linux/dist/LocalAI/LocalAI`

You may need Qt/X11 libraries (for example on Ubuntu: `libegl1`, `libxcb-cursor0`, `libxkbcommon0`).

## macOS

```bash
chmod +x packaging/macos/build.sh
bash packaging/macos/build.sh
```

Output: `packaging/macos/dist/LocalAI.app`

Ad-hoc or Developer ID signing is left to maintainers; the bundle is unsigned by default.

## Notes

- Entry point: `local_ai.__main__:main`
- Specs live next to each platform’s build script
- Dist/build folders are gitignored
