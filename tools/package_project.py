"""Make a ZIP from tracked Git files, excluding local environments and new runs."""
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    if not any(tracked):
        raise SystemExit('No tracked files. Stage the intended project files before packaging.')
    destination = ROOT / 'dist' / 'indoor-drone-mapping.zip'
    destination.parent.mkdir(exist_ok=True)
    count = 0
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in tracked:
            if name and (ROOT / name).is_file():
                archive.write(ROOT / name, 'indoor-drone-mapping/' + name)
                count += 1
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None, 'Archive verification failed'
    print(f'Packaged {count} tracked files: {destination}')


if __name__ == '__main__':
    main()
