#!/usr/bin/env python3
"""Post-restart TRIBE v2 load smoke for a Colab GPU runtime.

Prereq: run tools/colab_tribe_setup.py on the same session, then restart kernel.
This script intentionally does not install packages; mixing install+import in one
Colab kernel caused NumPy/SciPy binary-stack import failures.
"""
from __future__ import annotations

import json
import sys
import time

import numpy
import pandas
import scipy
import sklearn
import torch
import torchvision
from tribev2 import TribeModel

info = {
    "python": sys.version,
    "numpy": numpy.__version__,
    "scipy": scipy.__version__,
    "pandas": pandas.__version__,
    "sklearn": sklearn.__version__,
    "torch": torch.__version__,
    "torchvision": torchvision.__version__,
    "cuda_available": torch.cuda.is_available(),
    "device_count": torch.cuda.device_count(),
    "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}
print(json.dumps(info, indent=2), flush=True)
assert torch.cuda.is_available(), "Select a Colab L4/A100/H100 GPU runtime first"

t0 = time.time()
model = TribeModel.from_pretrained("facebook/tribev2", cache_folder="/content/tribe_cache")
print(json.dumps({"loaded_seconds": round(time.time() - t0, 2), "model_type": type(model).__name__}, indent=2), flush=True)
print("ok", flush=True)
