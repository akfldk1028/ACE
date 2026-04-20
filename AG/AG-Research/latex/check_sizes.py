import base64, os

files = ['references.bib', 'colm2026_conference.sty', 'colm2026_conference.bst', 'fancyhdr.sty', 'natbib.sty', 'main.tex', 'math_commands.tex']
for f in files:
    fp = os.path.join('D:/Data/25_ACE/AG/AG-Research/latex', f)
    if os.path.exists(fp):
        with open(fp, 'rb') as fh:
            data = fh.read()
        b64 = base64.b64encode(data).decode()
        print(f'{f}: {len(data)} bytes -> {len(b64)} b64 chars')
    else:
        print(f'{f}: NOT FOUND')
