import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, os

path = 'gen-comp19.rejected.json'
print('File exists:', os.path.exists(path))
sz = os.path.getsize(path)
print('File size:', sz)
with open(path, 'rb') as f:
    raw = f.read(1000)
print('First 1000 bytes:', raw)
