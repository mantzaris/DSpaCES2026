from pathlib import Path
import json
from iot_entropy.extension_reporting import build

root=Path(__file__).resolve().parents[1]
print(json.dumps(build(root),indent=2))
