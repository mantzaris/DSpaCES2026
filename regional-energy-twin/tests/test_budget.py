import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest
from evidence_fusion.resource_ledger import Budget


def test_expired_allocation_cannot_restart(tmp_path):
    old=(datetime.now(timezone.utc)-timedelta(hours=3)).isoformat()
    with pytest.raises(TimeoutError):Budget(tmp_path/'ledger.json',old,7200)


def test_main_launcher_refuses_without_authorization():
    result=subprocess.run([sys.executable,'scripts/run_main_study.py'],capture_output=True,text=True)
    assert result.returncode==2 and 'not authorized' in result.stderr


def test_main_launcher_refuses_failed_science_gate():
    # Explicit CLI flag does not silently enable the frozen false config.
    result=subprocess.run([sys.executable,'scripts/run_main_study.py','--authorize-main'],capture_output=True,text=True)
    assert result.returncode==2 and 'not authorized' in result.stderr
