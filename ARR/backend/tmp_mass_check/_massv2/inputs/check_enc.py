import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp19.json'

# Try different encodings
for enc in ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'cp1252']:
    try:
        with open(path, 'r', encoding=enc) as f:
            content = f.read(200)
        print(f'Encoding {enc} works, first 100 chars: {repr(content[:100])}')
        break
    except Exception as e:
        print(f'Encoding {enc} failed: {e}')
