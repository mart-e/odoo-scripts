#!/usr/bin/env python
# fetch latest translations from Transifex and commit them

import os
import subprocess
import sys
from datetime import datetime
from txclib import commands

# each path should contain a .tx/config file
CODE_PATHS = [
    'path/to/odoo/7.0',
    'path/to/odoo/8.0',
]
PULL_ARGS = [
    '--mode', 'reviewed',
]


# path_to_tx = len(sys.argv) > 1 and sys.argv[1] or utils.find_dot_tx()
def pull_project_translation(path_to_tx):
    """Fetch the translations from Transifex
    path_to_tx: path containing a .tx/config file
    """
    print("Fetching translations at %s" % datetime.now().isoformat())
    print("Pulling to %s" % path_to_tx)

    commands.cmd_pull(PULL_ARGS, path_to_tx)

    print("Done fetching at %s" % datetime.now().isoformat())


def commit_translations(code_path, commit=False):
    """Reset the code in :code_path: on current remote and push the new translations"""
    os.chdir(code_path)
    msg = "[I18N] Update translation terms from Transifex"
    branch = subprocess.check_output('git symbolic-ref -q --short HEAD', shell=True).replace('\n', '')  # branch name
    remote = subprocess.check_output(['git', 'config', 'branch.%s.remote' % branch]).replace('\n', '')  # remote name
    print("Fetching and pushing to %s/%s" % (remote, branch))
    if commit:
        # make have same code as remote
        subprocess.call(['git', 'fetch', remote, branch])
        subprocess.call(['git', 'reset', '%s/%s' % (remote, branch), '--hard'])

    pull_project_translation(code_path)

    if commit:
        # add new files
        subprocess.call(['git', 'add', '-A'])
        subprocess.call(['git', 'commit', '-m', msg])
        subprocess.call(['git', 'push', remote, branch])
    else:
        print("... skipped, dry run")

if __name__ == '__main__':
    commit = len(sys.argv) > 1 and sys.argv[1] == '--commit' or False
    for code_path in CODE_PATHS:
        commit_translations(code_path, commit)
