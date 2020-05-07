#!/usr/bin/env python
# fetch latest translations from Transifex and commit them

import argparse
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

import polib

REGEX = re.compile(
    "%(\(\w+\)|)([0+-]|)(\d+|\*|)[diouxXcrsa]|%(\(\w+\)|)([0+-]|)(\d+|\*|)(\.(\d+|\*|)|)[eEfFgG]|%%"
)
PULL_ARGS = [
    '--skip',
    # '--minimum-perc', '10',
]

def sanitize_pofile(po_path):
    po = polib.pofile(po_path)
    save = False
    for entry in po:
        rfrom, rto = False, False
        placeholders_src = sorted(
            [m.group(0) for m in REGEX.finditer(entry.msgid)]
        )
        placeholders_trans = sorted(
            [m.group(0) for m in REGEX.finditer(entry.msgstr)]
        )
        if entry.msgstr and placeholders_src != placeholders_trans:
            # placeholders present in source but not in translation
            missing_src = set(placeholders_src) - set(placeholders_trans)
            # placeholders present in translation but not in source
            added_trans = set(placeholders_trans) - set(placeholders_src)
            if len(missing_src) == 1 and len(added_trans) == 1:
                # just one is missing
                rfrom = added_trans.pop()
                rto = missing_src.pop()
                print(f"Bad translation rfixed {po_path} :\n\t{rfrom} -> {rto}")
            else:
                if "%s" in entry.msgid and "%s" not in entry.msgstr:
                    if "% s" in entry.msgstr:
                        if " %s" in entry.msgid:
                            rfrom, rto = "% s", " %s"
                        elif "%s " in entry.msgid:
                            rfrom, rto = "% s", "%s "
                        else:
                            rfrom, rto = "% s", "%s"
                    elif "%S" in entry.msgstr:
                        rfrom = "%S"
                    elif "S%" in entry.msgstr:
                        rfrom = "S%"
                    elif "s%" in entry.msgstr:
                        rfrom = "s%"
                    elif "%s" in entry.msgid and "%" in entry.msgstr:
                        rfrom = "%"
                        rto = "%s"
                    elif entry.msgid.startswith("%s"):
                        rfrom = entry.msgstr
                        rto = "%s " + rfrom
                    elif entry.msgid.endswith("%s"):
                        rfrom = entry.msgstr
                        rto = rfrom + " %s"
                    else:
                        rfrom, rto = entry.msgstr, ""
                else:
                    print(
                        f"Potential bad translation? in {po_path} :\n\t{entry.msgid[:100]}\n\t{entry.msgstr[:100]}"
                    )

        if rfrom:
            print(
                f"Bad translation in {po_path} :\n\t{entry.msgid[:100]}\n\t{entry.msgstr[:100]}"
            )
            entry.msgstr = entry.msgstr.replace(rfrom, rto)
            save = True

    if save:
        po.save()


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
    subprocess.call('touch -d "$(date -R --date=\'21 days ago\')" locale/*/LC_MESSAGES/*', shell=True)

    # commands.cmd_pull(PULL_ARGS, path_to_tx)
    subprocess.call(['tx', 'pull'] + PULL_ARGS)

    # remove changes with only Last-Translator or PO-Revision-Date
    subprocess.call("""git status --short | grep '.po' | grep  -v "^??" | sed 's/^ M *//' | sed 's/^?? *//' | xargs -I {} bash -c 'if test `git diff {} | grep "^+" | grep -v "^+++\|^+#\|Last-Translator\|PO-Revision-Date" | wc -l` -eq 0; then git checkout -- {}; fi'""", shell=True)
    print("Done fetching at %s" % datetime.now().isoformat())


def commit_translations(code_path, commit=False, push=False):
    """Reset the code in :code_path: on current remote and push the new translations"""
    os.chdir(code_path)
    msg = "[I18N] Update translation terms from Transifex"
    if commit:
        branch = subprocess.check_output('git symbolic-ref -q --short HEAD', shell=True, text=True).replace('\n', '')  # branch name
        remote = subprocess.check_output(['git', 'config', 'branch.%s.remote' % branch], text=True).replace('\n', '')  # remote name
        print("Working with to %s/%s" % (remote, branch))
        
        # make have same code as remote
        subprocess.call(['git', 'fetch', remote, branch])
        subprocess.call(['git', 'reset', '%s/%s' % (remote, branch), '--hard'])

    pull_project_translation(code_path)
    res = subprocess.run("""git status --short | grep '.po' | grep  -v "^??" | sed 's/^ M *//' | sed 's/^?? *//'""", shell=True, capture_output=True, text=True)
    for pofile in res.stdout.split('\n'):
        if pofile:
            sanitize_pofile(pofile)

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
