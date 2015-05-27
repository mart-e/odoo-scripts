#!/usr/bin/env python2

import os
import subprocess
from datetime import datetime
from txclib import commands

# path_to_tx = len(sys.argv) > 1 and sys.argv[1] or utils.find_dot_tx()
CODE_PATHS = [
    'path/to/odoo/7.0',
    'path/to/odoo/8.0',
]
PULL_ARGS = [
    '--mode', 'reviewed',
]


def pull_project_translation(path_to_tx):
    print("Starting pulling at %s" % datetime.now().isoformat())
    print("Pulling to %s" % path_to_tx)

    commands.cmd_pull(PULL_ARGS, path_to_tx)
    print("Done at %s" % datetime.now().isoformat())


def commit_translations():
    subprocess.call(['git', 'pull'])
    msg = "[I18N] Update translation terms from Transifex"
    subprocess.call(['git', 'commit', '-a', '-m', msg])
    subprocess.call(['git', 'push'])

if __name__ == '__main__':
    for code_path in CODE_PATHS:
        os.chdir(code_path)
        pull_project_translation(code_path)
        # commit_translations()
