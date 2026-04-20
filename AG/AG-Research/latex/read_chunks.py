import os, json

CHUNK_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex/chunks'

with open(os.path.join(CHUNK_DIR, 'manifest.json')) as f:
    manifest = json.load(f)

# Skip references.bib and colm2026_conference.sty (already uploaded)
skip = {'references.bib', 'colm2026_conference.sty'}

for entry in manifest:
    fname = entry['file']
    if fname in skip:
        continue
    n_chunks = entry['chunks']
    print(f"\n=== {fname} ({entry['size']} bytes, {n_chunks} chunks) ===")
    for i in range(n_chunks):
        chunk_path = os.path.join(CHUNK_DIR, f'{fname}.chunk{i}')
        with open(chunk_path) as f:
            data = f.read()
        print(f"  chunk{i}: {len(data)} chars")
