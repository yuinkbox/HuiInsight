import pathlib
p = pathlib.Path('e:/ahdunyi work/workTools/workspace/AHDUNYI_Terminal_PRO/client/build/build.py')
c = p.read_text(encoding='utf-8')
if 'encode("gbk"' in c:
    c = c.replace(
        '                # Strip non-ASCII chars that crash GBK terminals\n'
        '                safe = line.encode("gbk", errors="replace").decode("gbk", errors="replace")\n'
        '                print("    " + safe)',
        '                # Safe-print: avoid GBK encode errors on Windows CI\n'
        '                try:\n'
        '                    print("    " + line)\n'
        '                except UnicodeEncodeError:\n'
        '                    print("    " + line.encode("ascii", errors="replace").decode("ascii"))'
    )
    p.write_text(c, encoding='utf-8')
    print('fixed')
else:
    print('pattern not found')
