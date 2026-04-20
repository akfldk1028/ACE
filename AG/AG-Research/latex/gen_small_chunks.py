import base64, os, json

CHUNK_SIZE = 2000  # Much smaller chunks
SRC_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex'
OUT_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex/small_chunks'

files = ['references.bib', 'colm2026_conference.sty', 'colm2026_conference.bst',
         'fancyhdr.sty', 'natbib.sty', 'main.tex', 'math_commands.tex']

os.makedirs(OUT_DIR, exist_ok=True)

manifest = []
total_chunks = 0

for fname in files:
    fp = os.path.join(SRC_DIR, fname)
    with open(fp, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()

    chunks = [b64[i:i+CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)]
    total_chunks += len(chunks)
    manifest.append({'file': fname, 'chunks': len(chunks), 'size': len(data), 'b64_len': len(b64)})

    for idx, chunk in enumerate(chunks):
        chunk_file = os.path.join(OUT_DIR, f'{fname}.chunk{idx}')
        with open(chunk_file, 'w') as f:
            f.write(chunk)

    print(f'{fname}: {len(chunks)} chunks ({len(data)} bytes)')

with open(os.path.join(OUT_DIR, 'manifest.json'), 'w') as f:
    json.dump(manifest, f, indent=2)

print(f'\nTotal: {total_chunks} chunks')
