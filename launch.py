"""Open the supplied scene when no simulator is running, then run the mission."""
from pathlib import Path
import os
import socket
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent


def ready():
    try:
        with socket.create_connection(('127.0.0.1',23000),timeout=.5):
            return True
    except OSError:
        return False


def main():
    if not ready():
        candidates=[Path(os.environ.get('COPPELIASIM_ROOT',''))/'coppeliaSim.exe',
            Path(os.environ.get('ProgramFiles','C:/Program Files'))/'CoppeliaRobotics/CoppeliaSimEdu/coppeliaSim.exe']
        exe=next((p for p in candidates if p.is_file()),None)
        if exe is None:
            raise RuntimeError('Open CoppeliaSim and load IndoorDroneMapping.ttt, then try again.')
        subprocess.Popen([str(exe),str(ROOT/'IndoorDroneMapping.ttt')],cwd=str(exe.parent))
        deadline=time.monotonic()+60
        while not ready():
            if time.monotonic()>deadline:
                raise RuntimeError('CoppeliaSim did not become ready. Check its window for startup messages.')
            time.sleep(.5)
        time.sleep(2)
    from run import main as run_main
    sys.argv=[sys.argv[0]]
    run_main()


if __name__=='__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}',file=sys.stderr)
        sys.exit(1)
