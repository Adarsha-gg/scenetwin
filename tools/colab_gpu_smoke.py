import json, os, platform, sys, subprocess
print('python', sys.version)
print('platform', platform.platform())
try:
    import torch
    out = {
        'torch': torch.__version__,
        'cuda_available': torch.cuda.is_available(),
        'device_count': torch.cuda.device_count(),
        'device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    print(json.dumps(out, indent=2))
except Exception as e:
    print('torch_error', repr(e))
print('nvidia-smi:')
try:
    subprocess.run(['nvidia-smi'], check=False)
except Exception as e:
    print('nvidia_smi_error', repr(e))
