import base64, os

files = [
    'D:/Data/25_ACE/AG/AG-Research/latex/colm2026_conference.sty',
    'D:/Data/25_ACE/AG/AG-Research/latex/fancyhdr.sty',
    'D:/Data/25_ACE/AG/AG-Research/latex/colm2026_conference.bst',
    'D:/Data/25_ACE/AG/AG-Research/latex/natbib.sty',
    'D:/Data/25_ACE/AG/AG-Research/latex/main.tex',
    'D:/Data/25_ACE/AG/AG-Research/latex/references.bib',
]

script_lines = ['import base64, os', 'os.makedirs("/home/user/paper", exist_ok=True)', 'files = {']
for fpath in files:
    fname = os.path.basename(fpath)
    with open(fpath, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    script_lines.append(f'  "{fname}": "{b64}",')
script_lines.append('}')
script_lines.append('for name, b64data in files.items():')
script_lines.append('  with open(f"/home/user/paper/{name}", "wb") as f:')
script_lines.append('    f.write(base64.b64decode(b64data))')
script_lines.append('  print(f"Wrote {name}: {len(base64.b64decode(b64data))} bytes")')

script = '\n'.join(script_lines)
outpath = 'D:/Data/25_ACE/AG/AG-Research/latex/deploy_latex.py'
with open(outpath, 'w') as f:
    f.write(script)
print(f'Script size: {len(script)} bytes')
print(f'Written to {outpath}')
