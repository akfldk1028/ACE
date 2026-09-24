import sys, os
sys.path.insert(0, 'D:/Data/25_ACE/ARR/backend')
os.chdir('D:/Data/25_ACE/ARR/backend')
from design.maas import book_development
funcs = [x for x in dir(book_development) if not x.startswith('_')]
with open('D:/tmp_check_dev_out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(funcs) + '\n\n')
    # check validate function
    if hasattr(book_development, 'validate_development_payload'):
        import inspect
        sig = inspect.signature(book_development.validate_development_payload)
        f.write('validate_development_payload sig: ' + str(sig) + '\n')
    # check schema
    if hasattr(book_development, 'DEVELOPMENT_SCHEMA'):
        import json
        f.write('DEVELOPMENT_SCHEMA keys: ' + str(list(book_development.DEVELOPMENT_SCHEMA.keys())[:10]) + '\n')
print('Done')
