import base64, os

SRC_DIR = 'D:/Data/25_ACE/AG/AG-Research/latex'
files = ['references.bib', 'colm2026_conference.sty', 'colm2026_conference.bst',
         'fancyhdr.sty', 'natbib.sty', 'main.tex', 'math_commands.tex']

lines = []
lines.append('import base64, os')
lines.append('os.makedirs("/home/user/paper", exist_ok=True)')
lines.append('files = {')

for fname in files:
    fp = os.path.join(SRC_DIR, fname)
    with open(fp, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    lines.append(f'  "{fname}": "{b64}",')

lines.append('}')
lines.append('for name, b64data in files.items():')
lines.append('    with open(f"/home/user/paper/{name}", "wb") as f:')
lines.append('        f.write(base64.b64decode(b64data))')
lines.append('    print(f"Wrote {name}: {len(base64.b64decode(b64data))} bytes")')

code = '\n'.join(lines)
outpath = os.path.join(SRC_DIR, 'e2b_upload.py')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(code)
print(f'Generated {outpath}: {len(code)} chars')
