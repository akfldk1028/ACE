import base64, os, json

CHUNK_SIZE = 6000  # b64 chars per chunk, conservative
SRC_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex'
OUT_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex/chunks'

files = ['references.bib', 'colm2026_conference.sty', 'colm2026_conference.bst',
         'fancyhdr.sty', 'natbib.sty', 'main.tex', 'math_commands.tex']

os.makedirs(OUT_DIR, exist_ok=True)

manifest = []

for fname in files:
    fp = os.path.join(SRC_DIR, fname)
    with open(fp, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()

    chunks = []
    for i in range(0, len(b64), CHUNK_SIZE):
        chunks.append(b64[i:i+CHUNK_SIZE])

    manifest.append({'file': fname, 'chunks': len(chunks), 'size': len(data)})

    for idx, chunk in enumerate(chunks):
        chunk_file = os.path.join(OUT_DIR, f'{fname}.chunk{idx}')
        with open(chunk_file, 'w') as f:
            f.write(chunk)

    print(f'{fname}: {len(chunks)} chunks')

# Write manifest
with open(os.path.join(OUT_DIR, 'manifest.json'), 'w') as f:
    json.dump(manifest, f, indent=2)

print(f'\nTotal files: {len(files)}')
print(f'Manifest written to {OUT_DIR}/manifest.json')
