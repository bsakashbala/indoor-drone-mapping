from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
from contextlib import redirect_stdout
import io
import run


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp_root=Path(__file__).resolve().parents[1]/'output'/'test_tmp'
        self.temp_root.mkdir(parents=True,exist_ok=True)

    def args(self):
        return SimpleNamespace(no_gui=True,offline=False,port=23000,max_seconds=1)

    def test_running_unrelated_simulation_is_not_stopped(self):
        sim=Mock()
        sim.simulation_stopped=0
        sim.getSimulationState.return_value=1
        with tempfile.TemporaryDirectory(dir=self.temp_root) as tmp, patch.object(run,'ROOT',Path(tmp)), patch.object(run,'connection',return_value=(Mock(),sim)):
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError,'Stop the current simulation'):
                run.execute(self.args())
        sim.stopSimulation.assert_not_called()
        sim.startSimulation.assert_not_called()

    def test_connection_failure_remains_actionable(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as tmp, patch.object(run,'ROOT',Path(tmp)), patch.object(run,'connection',side_effect=RuntimeError('Cannot reach CoppeliaSim')):
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError,'Cannot reach CoppeliaSim'):
                run.execute(self.args())


if __name__=='__main__': unittest.main()
