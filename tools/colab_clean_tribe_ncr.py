from pathlib import Path
import shutil
p = Path('/content/tribe_ncr')
if p.exists():
    shutil.rmtree(p)
p.mkdir(parents=True, exist_ok=True)
print('cleaned /content/tribe_ncr')
