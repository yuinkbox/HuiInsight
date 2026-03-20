import pathlib
p = pathlib.Path('e:/ahdunyi work/workTools/workspace/AHDUNYI_Terminal_PRO/server/core/behavior_analyzer.py')
c = p.read_text(encoding='utf-8').rstrip() + '\n'
p.write_text(c, encoding='utf-8')
print('W391 fixed')
