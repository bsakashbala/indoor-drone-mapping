"""Report local setup problems without starting a simulation or changing files."""
import importlib
from importlib.metadata import version, PackageNotFoundError
import os
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    failures = []
    print(f'Python: {platform.python_version()} ({sys.executable})')
    if sys.version_info < (3, 10):
        failures.append('Install Python 3.10 or newer.')
    for module, package in [('PIL', 'Pillow'),
                            ('coppeliasim_zmqremoteapi_client', 'coppeliasim-zmqremoteapi-client'),
                            ('zmq', 'pyzmq'), ('cbor', 'cbor')]:
        try:
            importlib.import_module(module)
            print(f'OK: {package} {version(package)}')
        except (ImportError, PackageNotFoundError) as error:
            failures.append(f'{package}: {error}. Install the requirements with this Python.')
    try:
        import tkinter
        print(f'OK: tkinter, Tk {tkinter.TkVersion} (display availability is not tested)')
    except ImportError:
        print('NOTE: tkinter is unavailable. Use --no-gui or install Python with Tk support.')
    for filename in ['IndoorDroneMapping.ttt', 'IndoorDroneMapping_ObstacleDemo.ttt']:
        if (ROOT / filename).is_file():
            print(f'OK: {filename}')
        else:
            failures.append(f'Missing {filename}; extract the complete repository.')
    if os.name == 'nt':
        folder = Path(os.environ.get('COPPELIASIM_ROOT') or
                      str(Path(os.environ.get('ProgramFiles', 'C:/Program Files')) /
                          'CoppeliaRobotics/CoppeliaSimEdu'))
        if (folder / 'coppeliaSim.exe').is_file():
            print('OK: simulator executable found at the configured/default installation.')
        else:
            print('NOTE: automatic simulator location not found. Open it yourself or set COPPELIASIM_ROOT.')
    else:
        print('NOTE: the automatic launcher targets Windows. Open CoppeliaSim manually on other systems.')
    for error in failures:
        print('ERROR:', error)
    print('This check does not connect to the simulator or validate a flight.')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
