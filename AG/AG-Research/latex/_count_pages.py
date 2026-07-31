import re

with open('main.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Split at \appendix
parts = content.split('\\appendix')
main_body = parts[0]
appendix = parts[1] if len(parts) > 1 else ""

# Get content after \begin{document}
doc_start = main_body.split('\\begin{document}')
if len(doc_start) > 1:
    main_body = doc_start[1]

# Find all tables with labels
table_pattern = r'\\begin\{table\*?\}.*?\\caption\{(.*?)\}.*?\\label\{(.*?)\}.*?\\end\{table\*?\}'
tables = re.findall(table_pattern, main_body, re.DOTALL)

# Find all figures
fig_pattern = r'\\begin\{figure\*?\}.*?\\caption\{(.*?)\}.*?\\label\{(.*?)\}.*?\\end\{figure\*?\}'
figures = re.findall(fig_pattern, main_body, re.DOTALL)

# Count table rows (approximation of table size)
table_blocks = re.findall(r'(\\begin\{table\*?\}.*?\\end\{table\*?\})', main_body, re.DOTALL)

print("=== MAIN BODY TABLES ===")
for i, block in enumerate(table_blocks):
    label_m = re.search(r'\\label\{(.*?)\}', block)
    caption_m = re.search(r'\\caption\{(.*?)\}', block)
    rows = block.count('\\\\')
    label = label_m.group(1) if label_m else "unknown"
    caption = caption_m.group(1)[:60] if caption_m else "unknown"
    print(f"  {i+1}. {label}: {rows} rows - {caption}...")

print(f"\n=== MAIN BODY FIGURES ===")
fig_blocks = re.findall(r'(\\begin\{figure\*?\}.*?\\end\{figure\*?\})', main_body, re.DOTALL)
for i, block in enumerate(fig_blocks):
    label_m = re.search(r'\\label\{(.*?)\}', block)
    caption_m = re.search(r'\\caption\{(.*?)\}', block)
    label = label_m.group(1) if label_m else "unknown"
    caption = caption_m.group(1)[:60] if caption_m else "unknown"
    print(f"  {i+1}. {label}: {caption}...")

# Count per-section word counts
sections = re.split(r'(\\section\{[^}]+\})', main_body)
print(f"\n=== PER-SECTION WORD COUNT ===")
current_section = "Preamble/Abstract"
for part in sections:
    sec_match = re.match(r'\\section\{([^}]+)\}', part)
    if sec_match:
        current_section = sec_match.group(1)
        continue
    # Strip floats and commands
    text = re.sub(r'\\begin\{(table|figure|equation)\*?\}.*?\\end\{\1\*?\}', '', part, flags=re.DOTALL)
    text = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})*', ' ', text)
    text = re.sub(r'[{}\\$%&_^~\[\]]', ' ', text)
    words = len([w for w in text.split() if len(w) > 1])
    if words > 10:
        print(f"  {current_section}: {words} words")

# Appendix analysis
app_tables = len(re.findall(r'\\begin\{table', appendix))
app_figs = len(re.findall(r'\\begin\{figure', appendix))
print(f"\n=== APPENDIX ===")
print(f"  Tables: {app_tables}")
print(f"  Figures: {app_figs}")

print(f"\n=== CUTTING PLAN FOR 9-PAGE LIMIT ===")
print(f"Current: ~17 pages. Need to cut ~8 pages.")
print(f"")
print(f"KEEP in main body (essential):")
print(f"  tab:related       - positioning vs prior work")
print(f"  tab:patterns      - methodology (pattern configs)")
print(f"  tab:cross_category - core efficiency result")
print(f"  tab:difficulty    - key new finding (exp07)")
print(f"  fig:taxonomy      - essential overview")
print(f"  fig:exp01         - core result visualization")
print(f"")
print(f"MOVE to appendix:")
print(f"  tab:solo_baseline - merge key numbers into text")
print(f"  tab:regret        - summarize in 1 sentence")
print(f"  tab:adaptive      - summarize key finding in text")
print(f"  tab:lambda        - summarize in text")
print(f"  tab:cross_model   - summarize in text")
print(f"  fig:quality       - reference from text")
print(f"  fig:exp05         - reference from text")
print(f"")
print(f"TEXT cuts:")
print(f"  - Sec 4.3 (Convergence): condense to 1 paragraph")
print(f"  - Sec 4.4 (Error): condense to 1 paragraph")
print(f"  - Sec 4.5 (Adaptive): condense significantly")
print(f"  - Sec 5 (Discussion): trim guidelines to compact form")
print(f"  - Merge exp01 findings into fewer paragraphs")
