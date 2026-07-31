import base64, os

SRC_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex'
OUT_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex/e2b_scripts'
os.makedirs(OUT_DIR, exist_ok=True)

files = ['references.bib', 'colm2026_conference.sty', 'colm2026_conference.bst',
         'fancyhdr.sty', 'natbib.sty', 'main.tex', 'math_commands.tex']

for fname in files:
    fp = os.path.join(SRC_DIR, fname)
    with open(fp, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()

    code = f'''import base64, os
os.makedirs("/home/user/paper", exist_ok=True)
b64data = "{b64}"
with open("/home/user/paper/{fname}", "wb") as f:
    f.write(base64.b64decode(b64data))
print(f"Wrote {fname}: {{len(base64.b64decode(b64data))}} bytes")
'''
    outpath = os.path.join(OUT_DIR, f'upload_{fname}.py')
    with open(outpath, 'w') as f:
        f.write(code)
    print(f'{fname}: {len(code)} chars -> {outpath}')
