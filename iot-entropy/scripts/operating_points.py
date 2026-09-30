"""Regenerate the explicitly retrospective matched-control-budget diagnostic."""
from pathlib import Path
from iot_entropy.operating_points import build

build(Path(__file__).resolve().parents[1])
