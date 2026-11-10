"""Build the portable TRAKKNORMALIZER (one-dir inside a ZIP).

One-dir starts instantly: nothing is extracted on launch. The portable is
shipped as a ZIP the user unzips once:

    dist\\TRAKKNORMALIZER-portable-<version>.zip
        TRAKKNORMALIZER\\
            TRAKKNORMALIZER.exe
            _internal\\   (Qt, FFmpeg, ...)
            LICENSE / NOTICE.md / THIRD-PARTY-NOTICES.md / README.md

Usage (from the project folder):
    python build_portable.py

The old `build_exe.py` produced a one-file exe that re-extracted ~200 MB to
%TMP% on EVERY launch; it was removed on purpose.
"""

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXE_DIR = ROOT / "dist" / "portable" / "TRAKKNORMALIZER"
DOCS = ("LICENSE", "NOTICE.md", "THIRD-PARTY-NOTICES.md", "README.md")

FFMPEG_CANDIDATES = [
    Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-9.0.1-full_build" / "bin",
    Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    / "Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-8.1.1-essentials_build" / "bin",
]


def find_binary(name: str) -> Path | None:
    exe = shutil.which(name)
    if exe:
        return Path(exe)
    for folder in FFMPEG_CANDIDATES:
        candidate = folder / f"{name}.exe"
        if candidate.exists():
            return candidate
    return None


def project_version() -> str:
    """Read the version from gui.py (single source: setApplicationVersion)."""
    text = (ROOT / "gui.py").read_text(encoding="utf-8")
    m = re.search(r'setApplicationVersion\("([^"]+)"\)', text)
    return m.group(1) if m else "dev"


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT))


def main() -> int:
    ffmpeg = find_binary("ffmpeg")
    ffprobe = find_binary("ffprobe")
    if ffmpeg is None or ffprobe is None:
        print("ERROR: ffmpeg.exe / ffprobe.exe not found (add FFmpeg to PATH).")
        return 1

    version = project_version()
    print(f"TRAKKNORMALIZER portable version: {version}")

    if EXE_DIR.exists():
        shutil.rmtree(EXE_DIR, ignore_errors=True)

    icon = ROOT / "icon.ico"
    icon_args = ["--icon", str(icon)] if icon.exists() else []

    rc = run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onedir", "--windowed",
        *icon_args,
        "--name", "TRAKKNORMALIZER",
        "--distpath", "dist/portable",
        "--workpath", "build/portable",
        "--specpath", "build/portable",
        "--add-data", f"{ROOT / 'styles.qss'};.",
        "--add-binary", f"{ffmpeg};.",
        "--add-binary", f"{ffprobe};.",
        str(ROOT / "main.py"),
    ])
    if rc != 0:
        return rc

    exe = EXE_DIR / "TRAKKNORMALIZER.exe"
    if not exe.is_file():
        print(f"ERROR: {exe} was not created.")
        return 1

    for name in DOCS:
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, EXE_DIR / name)

    out = ROOT / "dist" / f"TRAKKNORMALIZER-portable-{version}.zip"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in sorted(EXE_DIR.rglob("*")):
            if p.is_file():
                zf.write(p, Path("TRAKKNORMALIZER") / p.relative_to(EXE_DIR))

    print(f"OK: {out} ({out.stat().st_size / 1e6:.1f} MB)")
    print("Unzip once, then run TRAKKNORMALIZER\\TRAKKNORMALIZER.exe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
