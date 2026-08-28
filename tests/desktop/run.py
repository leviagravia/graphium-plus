#!/usr/bin/env python3
from __future__ import annotations
import argparse
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from tests.desktop.harness.runtime import isolated_env

SECTIONS = ['lifecycle', 'actions', 'editing', 'search', 'view', 'printing', 'tab_controls', 'plus_toolbar', 'plus_workspace', 'dnd', 'monitoring', 'performance']


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--section', action='append', choices=SECTIONS)
    parser.add_argument('--manual', action='store_true')
    args = parser.parse_args()
    repo = REPO_ROOT
    for section in args.section or SECTIONS:
        print(f'DESKTOP_SECTION={section} START', flush=True)
        with isolated_env(prefix=f'graphium-desktop-{section}-') as (_, env):
            cmd = [sys.executable, '-B', '-m', f'tests.desktop.scenarios.{section}', '--repo', str(repo)]
            if args.manual:
                cmd.append('--manual')
            import subprocess
            completed = subprocess.run(cmd, cwd=repo, env=env)
        if completed.returncode:
            result = 'FAIL' if completed.returncode == 1 else 'STOP'
            print(f'DESKTOP_SECTION={section} RESULT={result}', flush=True)
            return completed.returncode if completed.returncode in (1, 2) else 2
        print(f'DESKTOP_SECTION={section} RESULT=PASS', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
