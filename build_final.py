#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AHDUNYI Client - One-click build script
Compatible with Windows GBK terminals (no emoji, encoding-safe subprocess).
"""

import os
import sys
import subprocess
import shutil
import locale
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_build_dirs():
    """Remove previous build artifacts."""
    for dir_name in ('dist', 'build'):
        p = Path(dir_name)
        if p.exists():
            shutil.rmtree(p)
            print('[OK] Cleaned: ' + dir_name)


def check_environment():
    """Verify all required packages are installed."""
    print('[*] Checking build environment')
    print('-' * 40)

    v = sys.version_info
    print(f'[*] Python: {v.major}.{v.minor}.{v.micro}')

    # PyInstaller
    print('\n[*] Build tools:')
    pyinstaller_ok = False
    for name in ('PyInstaller', 'pyinstaller'):
        try:
            __import__(name)
            print('[OK] PyInstaller: installed')
            pyinstaller_ok = True
            break
        except ImportError:
            continue
    if not pyinstaller_ok:
        print('[ERR] PyInstaller not found. Run: pip install pyinstaller')
        return False

    # Runtime dependencies
    print('\n[*] Runtime dependencies:')
    deps = [
        ('psutil',       ['psutil']),
        ('uiautomation', ['uiautomation']),
        ('PyQt6',        ['PyQt6', 'PyQt6.QtWidgets']),
        ('requests',     ['requests']),
    ]
    missing = []
    for display, names in deps:
        ok = False
        for n in names:
            try:
                __import__(n)
                print(f'[OK] {display}')
                ok = True
                break
            except ImportError:
                pass
        if not ok:
            print(f'[MISS] {display}')
            missing.append(display)

    if missing:
        print('\n[ERR] Missing: ' + ', '.join(missing))
        print('Run: pip install ' + ' '.join(missing))
        return False

    print('\n[OK] Environment check passed')
    return True


def build_client():
    """Run PyInstaller with encoding-safe subprocess handling."""
    print('\n[*] Starting PyInstaller build')
    print('-' * 40)

    spec_file = 'AHDUNYI_CLIENT_FINAL.spec'
    if not os.path.exists(spec_file):
        print('[ERR] Spec file not found: ' + spec_file)
        return False

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        spec_file,
        '--distpath', 'dist',
        '--workpath', 'build',
        '--clean',
        '--noconfirm',
    ]
    print('[CMD] ' + ' '.join(cmd))
    print('=' * 60)

    # Determine the safest encoding for this Windows terminal.
    # Always add errors='replace' so a single bad byte never crashes the script.
    enc = locale.getpreferredencoding(False) or 'utf-8'

    process = None
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr into stdout
            text=True,
            encoding=enc,
            errors='replace',           # replace undecodable bytes with ?
        )

        output_lines = []
        for raw_line in process.stdout:
            line = raw_line.rstrip()
            if line:
                print('  ' + line)
                output_lines.append(line)

        process.wait(timeout=300)

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)

        print('\n[OK] Build succeeded!')
        print('-' * 40)

        # Show produced executables
        exe_files = list(Path('dist').rglob('*.exe'))
        if exe_files:
            print('[*] Output executables:')
            for exe in exe_files:
                mb = exe.stat().st_size / (1024 * 1024)
                print(f'  {exe.name}  ({mb:.1f} MB)')
                print(f'  Path: {exe.absolute()}')
                if mb < 1:
                    print('  [WARN] File suspiciously small - build may be incomplete')
                elif mb > 100:
                    print('  [WARN] File suspiciously large - check excluded modules')
        else:
            print('[WARN] No .exe found under dist/')

        # Key build lines summary
        keywords = (
            'INFO: PyInstaller:',
            'INFO: Python:',
            'INFO: Platform:',
            'completed successfully',
        )
        key = [l for l in output_lines if any(k in l for k in keywords)]
        if key:
            print('\n[*] Build summary (last 10 key lines):')
            for l in key[-10:]:
                print('  ' + l)

        return True

    except subprocess.CalledProcessError as e:
        print('\n[ERR] Build failed with return code: ' + str(e.returncode))
        print('See output above for details.')
        return False

    except subprocess.TimeoutExpired:
        if process:
            process.kill()
        print('\n[ERR] Build timed out after 5 minutes.')
        return False


def verify_architecture():
    """Check that required UI Automation components exist in the source tree."""
    print('\n[*] Verifying architecture purity (UI Automation)')
    print('-' * 40)

    required = ['uiautomation', 'PyQt6', 'psutil']
    missing = []

    for kw in required:
        found = False
        for root, dirs, files in os.walk('.'):
            for fname in files:
                if fname.endswith(('.py', '.spec', '.md')):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                            if kw.lower() in f.read().lower():
                                found = True
                                break
                    except Exception:
                        continue
            if found:
                break
        if not found:
            missing.append(kw)

    if not missing:
        print('[OK] Architecture verified: all UI Automation components present')
    else:
        print('[WARN] Missing components: ' + ', '.join(missing))

    return len(missing) == 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print('=' * 60)
    print('AHDUNYI Client - One-click build')
    print('Version: 2.0.0 | Architecture: 100% pure UI Automation')
    print('=' * 60)

    # 1. Architecture purity check
    if not verify_architecture():
        print('\n[ERR] Architecture verification failed. Aborting.')
        return 1

    # 2. Clean previous artifacts
    clean_build_dirs()

    # 3. Environment check
    if not check_environment():
        return 1

    # 4. Build
    if not build_client():
        return 1

    print('\n' + '=' * 60)
    print('[OK] Build complete!')
    print('=' * 60)
    print('\nUsage:')
    print('  Run  : dist\\AHDUNYI_Audit_Client\\AHDUNYI_Audit_Client.exe')
    print('  Cfg  : config.example.json (copy to same dir as exe)')
    print('  Logs : logs\\client.log')
    return 0


if __name__ == '__main__':
    sys.exit(main())
