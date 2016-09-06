#!/usr/bin/env python2

import argparse
import os
import subprocess
from os.path import join as j

ADDONS_SUBPATHS = ['', 'addons', 'openerp/addons']
MASTER_LANG = ['nl', 'zh_CN', 'fr', 'hu', 'pt_BR', 'es']


def merge_po(src_path, new_path, dest_path):
    for addons_subpath in ADDONS_SUBPATHS:
        if not os.path.exists(j(dest_path, addons_subpath)):
            print("skip subpath '%s'..." % j(dest_path, addons_subpath))
            continue

        for addon in os.listdir(j(dest_path, addons_subpath)):
            i18n_path = j(dest_path, addons_subpath, addon, 'i18n')
            if not os.path.exists(i18n_path):
                print("skip '%s'..." % i18n_path)
                continue

            print("Processing '%s'..." % addon)
            for lang in sorted(filter(lambda x: x.endswith('.po'), os.listdir(i18n_path))):
                src = j(src_path, addons_subpath, addon, 'i18n', lang)
                new = j(new_path, addons_subpath, addon, 'i18n', lang)
                dest = j(dest_path, addons_subpath, addon, 'i18n', lang)
                ref = j(dest_path, addons_subpath, addon, 'i18n', addon+'.pot')
                language = lang.replace('.po', '')
                if not os.path.exists(src):
                    subprocess.call(['cp', new, dest])
                elif not os.path.exists(new) or language not in MASTER_LANG:
                    subprocess.call(['cp', src, dest])
                else:
                # cmd = 'msgcat %(src)s %(new)s -o %(dest)s'
                    subprocess.call(['msgcat', '--use-first', src, new, '-o', dest])
                cmd = "msgmerge --no-fuzzy-matching -q %(dest)s %(ref)s | msgattrib --no-obsolete -o %(dest)s" % {'ref': ref, 'dest': dest}
                subprocess.call(cmd, shell=True)
                # subprocess.call(['msgmerge', dest, ref, '--update', '-N'])

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True,
                        help='path to source directory')
    parser.add_argument('--new', required=True,
                        help='path to new translations')
    parser.add_argument('--dest', required=True,
                        help='path where generated po will be stored')

    args = parser.parse_args()
    merge_po(args.base, args.new, args.dest)
