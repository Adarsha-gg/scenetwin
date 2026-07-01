# Code Context

## Files Retrieved
1. `tools/colab_tribe_smoke.py` (lines 1-15) - current failing smoke installs TRIBE directly from GitHub, then imports `TribeModel` and calls `TribeModel.from_pretrained` without pinning ABI-sensitive deps or restarting the runtime.
2. `facebookresearch/tribev2@main/pyproject.toml` (public; fetched 2026-06-23) - TRIBE declares `requires-python >=3.11`, `torch>=2.5.1,<2.7`, `torchvision>=0.20,<0.22`, and `numpy==2.2.6`.
3. `facebookresearch/tribev2@main/README.md` (public; fetched 2026-06-23) - README shows `from tribev2 import TribeModel` and `TribeModel.from_pretrained("facebook/tribev2", cache_folder="./cache")` as the canonical load check.
4. PyPI wheel metadata for `neuralset==0.0.2`, `neuraltrain==0.0.2`, `exca==0.5.20` (queried 2026-06-23) - transitive deps require NumPy >=2.1, pandas >=2.2.2, scikit-learn, torch >=2.5.1, torchvision >=0.20.1.

## Key Code

Current local entry point:

```python
# tools/colab_tribe_smoke.py lines 7-15
run([sys.executable, '-m', 'pip', 'install', '-q', 'git+https://github.com/facebookresearch/tribev2.git', 'yt-dlp', 'gtts'])
from tribev2 import TribeModel
import torch
model = TribeModel.from_pretrained('facebook/tribev2', cache_folder='/content/tribe_cache')
```

Root cause pattern: Colab Python 3.12 keeps many compiled packages preinstalled/importable. Installing `tribev2` after runtime start can leave a mixed binary stack: TRIBE pins `numpy==2.2.6`, while already-installed/imported SciPy/sklearn/pandas/torchvision wheels may have been resolved against different NumPy/Torch ABIs. The `_center` import error from `numpy._core.umath` is consistent with this kind of stale/mismatched compiled extension state. A runtime restart after force-installing a coherent set is not optional.

## Architecture

`tools/colab_tribe_smoke.py` is a Colab-side smoke script, not the model code. Its only required success criterion is: install TRIBE + deps, start a fresh Python process/runtime after the binary install, import `tribev2`, and instantiate `TribeModel.from_pretrained('facebook/tribev2')` on a CUDA runtime. The model load is independent of SceneTwin data.

## Minimal robust Colab sequence

Use two cells or two CLI phases. Do not combine install and import in the same live kernel.

### Cell/phase 1: install pinned binary stack, then restart

```bash
python -m pip install -U pip setuptools wheel
python -m pip uninstall -y tribev2 neuralset neuraltrain exca numpy scipy pandas scikit-learn torch torchvision torchaudio || true
python -m pip install --no-cache-dir \
  'numpy==2.2.6' \
  'scipy==1.15.3' \
  'pandas==2.2.3' \
  'scikit-learn==1.6.1' \
  'torch==2.6.0' \
  'torchvision==0.21.0'
python -m pip install --no-cache-dir \
  'git+https://github.com/facebookresearch/tribev2.git' \
  'yt-dlp' 'gtts'
python -m pip check
```

Then restart the Colab runtime/kernel:

```python
import os
os.kill(os.getpid(), 9)
```

Notes:
- The pins match TRIBE's declared `numpy==2.2.6`, `torch>=2.5.1,<2.7`, and `torchvision>=0.20,<0.22` constraints.
- `scipy==1.15.3`, `pandas==2.2.3`, and `scikit-learn==1.6.1` have Python 3.12 wheels and are compatible with NumPy 2.x.
- L4 and A100 both work through the same CUDA-enabled Colab PyTorch wheel; no GPU-specific package split is needed.

### Cell/phase 2: verify after restart

```python
import json, time, sys
import numpy, scipy, pandas, sklearn, torch, torchvision
from tribev2 import TribeModel

print(json.dumps({
    'python': sys.version,
    'numpy': numpy.__version__,
    'scipy': scipy.__version__,
    'pandas': pandas.__version__,
    'sklearn': sklearn.__version__,
    'torch': torch.__version__,
    'torchvision': torchvision.__version__,
    'cuda': torch.cuda.is_available(),
    'device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}, indent=2))

assert torch.cuda.is_available(), 'Select a Colab L4 or A100 GPU runtime first'
t0 = time.time()
model = TribeModel.from_pretrained('facebook/tribev2', cache_folder='/content/tribe_cache')
print('loaded_seconds', round(time.time() - t0, 2))
print(type(model).__name__)
print('ok')
```

Expected verifier output on L4/A100: CUDA true, device name containing `L4` or `A100`, NumPy `2.2.6`, Torch `2.6.0...`, then `TribeModel` and `ok`.

## Script change to `tools/colab_tribe_smoke.py` if editing later

Keep the file as a post-restart smoke only. Move installation into a separate bootstrap script/cell because a script cannot reliably restart and continue inside the same Colab process. If one script must handle both phases, gate it with an env var:

```python
if os.environ.get('TRIBE_POST_RESTART') != '1':
    # install pinned stack, pip check, print instructions, os.kill(os.getpid(), 9)
else:
    # import/version print/from_pretrained verification only
```

## Start Here

Open `tools/colab_tribe_smoke.py` first. The needed change is not in model loading; it is the install/restart boundary before line 10 imports `tribev2`.

## Supervisor coordination

No supervisor decision needed.

## Acceptance

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Investigation only; no source files modified. Report provides minimal Colab install/restart/verify sequence scoped to fixing TribeModel.from_pretrained import/load failure."
    }
  ],
  "changedFiles": [
    "subagent-reports/tribe-colab-fix.md"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "grep/find for tribev2, TribeModel, and tools/colab_tribe_smoke.py",
      "result": "passed",
      "summary": "Located current smoke entry point and related Colab notebooks."
    },
    {
      "command": "read tools/colab_tribe_smoke.py",
      "result": "passed",
      "summary": "Confirmed current script installs unpinned GitHub TRIBE and imports in same runtime."
    },
    {
      "command": "fetch public facebookresearch/tribev2 pyproject.toml and README.md",
      "result": "passed",
      "summary": "Confirmed TRIBE dependency constraints: Python >=3.11, numpy==2.2.6, torch>=2.5.1,<2.7, torchvision>=0.20,<0.22."
    },
    {
      "command": "pip download --no-deps neuralset==0.0.2 neuraltrain==0.0.2 exca==0.5.20 and inspect METADATA",
      "result": "passed",
      "summary": "Confirmed transitive dependencies on NumPy >=2.1, pandas, scikit-learn, torch, and torchvision."
    },
    {
      "command": "git status --short",
      "result": "passed",
      "summary": "Repository already had pre-existing modified/untracked files; this task only wrote the requested report."
    }
  ],
  "validationOutput": [
    "Report written to subagent-reports/tribe-colab-fix.md"
  ],
  "residualRisks": [
    "Sequence was derived from dependency metadata and Colab ABI behavior; not executed on an actual Colab L4/A100 in this local session.",
    "Repository has many pre-existing unstaged/untracked files unrelated to this task."
  ],
  "noStagedFiles": true,
  "notes": "No project files were modified except the requested report artifact."
}
```
