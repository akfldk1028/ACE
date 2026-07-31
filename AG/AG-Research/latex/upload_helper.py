import base64, sys, os

# Generate base64 for a given file
fname = sys.argv[1]
fpath = os.path.join('D:/Data/25_ACE/AG/AG-Research/latex', fname)
with open(fpath, 'rb') as f:
    data = f.read()
b64 = base64.b64encode(data).decode()

# Split into chunks of 5000 chars
CHUNK = 5000
chunks = [b64[i:i+CHUNK] for i in range(0, len(b64), CHUNK)]

print(f"FILE: {fname}")
print(f"SIZE: {len(data)}")
print(f"B64_LEN: {len(b64)}")
print(f"CHUNKS: {len(chunks)}")
for i, c in enumerate(chunks):
    print(f"CHUNK_{i}: {c}")
