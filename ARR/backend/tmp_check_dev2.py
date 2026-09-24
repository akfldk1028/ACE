import sys, os, json
sys.path.insert(0, 'D:/Data/25_ACE/ARR/backend')
os.chdir('D:/Data/25_ACE/ARR/backend')
from design.maas import book_development
import inspect

with open('D:/tmp_check_dev2_out.txt', 'w', encoding='utf-8') as f:
    # Get source of validate_development_payload
    try:
        src = inspect.getsource(book_development.validate_development_payload)
        f.write('=== validate_development_payload ===\n')
        f.write(src[:3000] + '\n\n')
    except Exception as e:
        f.write(f'Error getting source: {e}\n')
    
    # Get GeometryProgram class
    try:
        src2 = inspect.getsource(book_development.GeometryProgram)
        f.write('=== GeometryProgram ===\n')
        f.write(src2[:3000] + '\n\n')
    except Exception as e:
        f.write(f'Error getting GeometryProgram: {e}\n')

print('Done')
