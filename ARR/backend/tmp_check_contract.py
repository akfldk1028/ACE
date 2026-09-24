import sys, os, json
sys.path.insert(0, 'D:/Data/25_ACE/ARR/backend')
os.chdir('D:/Data/25_ACE/ARR/backend')

from design.maas import book_development
import inspect

src = inspect.getsource(book_development.validate_parent_contract)
with open('D:/tmp_contract_out.txt', 'w', encoding='utf-8') as f:
    f.write(src + '\n')
print('Done')
