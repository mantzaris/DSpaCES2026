import gzip
import shutil
from pathlib import Path

root=Path(__file__).resolve().parents[1]
dashboard=root/'dashboard';destination=dashboard/'data/extension';destination.mkdir(parents=True,exist_ok=True)
legacy=dashboard/'spatial-v1.html'
if not legacy.exists():shutil.copy2(dashboard/'index.html',legacy)
shutil.copy2(root/'src/iot_entropy/extension_dashboard.html',dashboard/'index.html')
for path in (root/'results/extension-v2/replays').glob('*.json.gz'):
    (destination/path.name[:-3]).write_bytes(gzip.decompress(path.read_bytes()))
print('Built dashboard/index.html; serve the dashboard directory over HTTP.')
