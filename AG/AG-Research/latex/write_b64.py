import base64, sys
fname = sys.argv[1]
with open(f'D:/Data/25_ACE/AG/AG-Research/latex/{fname}', 'rb') as f:
    data = f.read()
b64 = base64.b64encode(data).decode()
with open(f'D:/Data/25_ACE/AG/AG-Research/latex/{fname}.b64', 'w') as f:
    f.write(b64)
print(f'{fname}: {len(data)} bytes -> {len(b64)} b64 chars')
