# Reproduce the Sony published-source comparison offline

The [Sony WebKit page](https://www.playstation.com/en-us/oss/ps5/webkit/) links the public `WebKit_1400.zip` under “14.00 -”. If you already have an authorized local copy, the following PowerShell example reads only the two named source members, checks their independently recorded SHA-256 values and ZIP CRCs, and writes a **new** ignored source subset. It does not execute source, inspect a console, or assert a whole-ZIP hash.

Run from the repository root, setting the local ZIP path first:

```powershell
$env:PS5_CSSFONTFACE_ZIP = 'E:\local-source\WebKit_1400.zip'
@'
import hashlib, json, os
from pathlib import Path
from zipfile import ZipFile

manifest_path = Path('research/examples/cssfontface/sony-1400-snapshot.json')
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
output = Path('derived/sony-1400-source-subset')
if output.exists():
    raise FileExistsError('Choose a new output directory')
selected = {}
with ZipFile(os.environ['PS5_CSSFONTFACE_ZIP']) as archive:
    for entry in manifest['files']:
        content = archive.read(entry['archive_member'])
        if hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise ValueError('Source member SHA-256 mismatch: ' + entry['path'])
        selected[entry['path']] = content
output.mkdir(parents=True)
for name, content in selected.items():
    path = output / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
(output / 'snapshot.json').write_bytes(manifest_path.read_bytes())
print('Two source members verified; no firmware mapping established.')
'@ | python -S -
python -S tools/ps5_research.py --webkit-snapshot derived\sony-1400-source-subset\snapshot.json --format json --output derived\sony-1400-source-audit.json
python -S tools/ps5_research.py --webkit-snapshot derived\sony-1400-source-subset\snapshot.json --output derived\sony-1400-source-audit.md
```

The classification refers to the source pair. The exact firmware 14.10 verdict remains insufficient. If the current Sony bundle no longer has these member hashes, retain the new archive separately and report the changed source as unverified/modified; do not silently update the pins or assume a patch from a filename.
