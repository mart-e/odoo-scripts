#!/usr/bin/env python
# fetch latest translations from Transifex and commit them

import argparse
import os
import subprocess
from datetime import datetime

PULL_ARGS = [
    '--skip',
    '--minimum-perc', '10',
]


# path_to_tx = len(sys.argv) > 1 and sys.argv[1] or utils.find_dot_tx()
def pull_project_translation(path_to_tx):
    """Fetch the translations from Transifex
    path_to_tx: path containing a .tx/config file
    """
    print("Fetching translations at %s" % datetime.now().isoformat())
    print("Pulling to %s" % path_to_tx)

    # tx uses timestamp to know if we should fetch translations, git doesn't give a shit about timestamp
    subprocess.call('touch -d "$(date -R --date=\'21 days ago\')" */i18n/*', shell=True)
    subprocess.call('touch -d "$(date -R --date=\'21 days ago\')" addons/*/i18n/*', shell=True)
    subprocess.call('touch -d "$(date -R --date=\'21 days ago\')" openerp/addons/*/i18n/*', shell=True)
    subprocess.call('touch -d "$(date -R --date=\'21 days ago\')" odoo/addons/*/i18n/*', shell=True)

    # commands.cmd_pull(PULL_ARGS, path_to_tx)
    subprocess.call(['tx', 'pull'] + PULL_ARGS)

    # remove changes with only Last-Translator or PO-Revision-Date
    subprocess.call("""git status --short | grep '.po' | grep  -v "^??" | sed 's/^ M *//' | sed 's/^?? *//' | xargs -I {} bash -c 'if test `git diff {} | grep "^+" | grep -v "^+++\|^+#\|Last-Translator\|PO-Revision-Date" | wc -l` -eq 0; then git checkout -- {}; fi'""", shell=True)
    print("Done fetching at %s" % datetime.now().isoformat())


def commit_translations(code_path, commit=False, push=False):
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
        if push:
            subprocess.call(['git', 'push', remote, branch])
    else:
        print("... skipped, dry run")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True,
                        help='path to code directory, containins .tx/config file')
    parser.add_argument('--commit', action='store_true',
                        help='Make a local commit of fetched translations')
    parser.add_argument('--push', action='store_true',
                        help='Push local commit to remote')

    args = parser.parse_args()
    if (args.push and not args.commit) or not os.path.isdir(args.path):
        parser.print_help()
    else:
        commit_translations(args.path, args.commit, args.push)
