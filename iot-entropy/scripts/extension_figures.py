from pathlib import Path
from iot_entropy.extension_figures import build_figures, numeric_tables

root=Path(__file__).resolve().parents[1]
build_figures(root)
numeric_tables(root)
