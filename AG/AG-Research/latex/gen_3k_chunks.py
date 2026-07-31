import base64, os, json

CHUNK_SIZE = 3000
SRC_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex'
OUT_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex/chunks3k'
os.makedirs(OUT_DIR, exist_ok=True)

# Only files that need chunked upload (>8KB)
files = ['colm2026_conference.bst', 'math_commands.tex', 'main.tex']

for fname in files:
    fp = os.path.join(SRC_DIR, fname)
    with open(fp, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    chunks = [b64[i:i+CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)]
    for idx, chunk in enumerate(chunks):
        with open(os.path.join(OUT_DIR, f'{fname}.{idx}'), 'w') as f:
            f.write(chunk)
    print(f'{fname}: {len(data)} bytes, {len(b64)} b64, {len(chunks)} chunks')
