import sys, os, json
sys.path.insert(0, 'D:/Data/25_ACE/ARR/backend')
os.chdir('D:/Data/25_ACE/ARR/backend')

with open('D:/tmp_check_dev3_out.txt', 'w', encoding='utf-8') as f:
    # Check LLM adapter
    try:
        from design.maas.geometry_language import llm_adapter
        import inspect
        src = inspect.getsource(llm_adapter._program_from_structured_author_item)
        f.write('=== _program_from_structured_author_item ===\n')
        f.write(src[:5000] + '\n\n')
    except Exception as e:
        f.write(f'Error: {e}\n')

    # Check what OPERATORS exist
    try:
        from design.maas.geometry_language import operators as ops_module
        op_names = [x for x in dir(ops_module) if not x.startswith('_')]
        f.write('=== Operators ===\n')
        f.write('\n'.join(op_names[:50]) + '\n\n')
    except Exception as e:
        f.write(f'Error ops: {e}\n')
    
    # Check macro operators
    try:
        from design.maas.geometry_language.llm_adapter import MACRO_SCHEMA
        f.write('=== MACRO_SCHEMA ===\n')
        f.write(json.dumps(MACRO_SCHEMA, indent=2, default=str)[:5000] + '\n\n')
    except Exception as e:
        f.write(f'Error MACRO_SCHEMA: {e}\n')

print('Done')
