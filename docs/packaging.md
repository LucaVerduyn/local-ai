# Packaging

## Windows (PyInstaller)

From the repository root, with your virtual environment active:

```powershell
pip install -e ".[packaging]"
powershell -File packaging/windows/build.ps1
```

Output: `packaging/windows/dist/LocalAI/LocalAI.exe`

## Future platforms

- `packaging/linux/` — AppImage or deb (planned)
- `packaging/macos/` — `.app` bundle (planned)

Keep entry point `local_ai.__main__:main` stable so specs stay simple.
