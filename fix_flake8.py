import pathlib

p = pathlib.Path('e:/ahdunyi work/workTools/workspace/AHDUNYI_Terminal_PRO/server/core/behavior_analyzer.py')
lines = p.read_text(encoding='utf-8').splitlines(keepends=True)

result = []
for i, line in enumerate(lines, 1):
    # Fix F401: remove unused imports (datetime, Tuple)
    if 'from datetime import datetime' in line:
        continue
    if 'from typing import' in line and 'Tuple' in line:
        line = line.replace(', Tuple', '').replace('Tuple, ', '')
    # Fix W293: blank lines with whitespace
    if line.strip() == '':
        line = '\n'
    result.append(line)

# Fix E301 at line 143: ensure blank line before set_report_count
# Find 'def set_report_count' and ensure 1 blank line before it
fixed = []
for i, line in enumerate(result):
    if 'def set_report_count' in line:
        # check previous non-empty
        if fixed and fixed[-1].strip() != '':
            fixed.append('\n')
    fixed.append(line)

p.write_text(''.join(fixed), encoding='utf-8')
print('all fixes applied')
