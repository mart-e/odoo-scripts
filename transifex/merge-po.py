#!/usr/bin/env python2
# usage:
#  $ python merge-po.py --ref $REF --trad $SRC --dest $DEST
# where - $REF is where the reference .pot is stored
#       - $SRC is where the translations to use are stored
#       - $DEST is where to store the new translations
#       ($REF and $DEST are probably the same)
#       arguments are path to source repositories

import argparse
import os
import subprocess
from os.path import join as j

ADDONS_SUBPATHS = ['', 'addons', 'openerp/addons', 'odoo/addons']

def merge_po(src_path, new_path, dest_path, filter_lang=False):

    def guess_openerp(firstpart, file, addons_subpath, addon):
        guesspath = j(firstpart, addons_subpath, addon, 'i18n', file)
        if addons_subpath == 'openerp/addons' and not os.path.exists(guesspath):
            return j(firstpart, 'odoo/addons', addon, 'i18n', file)
        elif addons_subpath == 'odoo/addons' and not os.path.exists(guesspath):
            return j(firstpart, 'openerp/addons', addon, 'i18n', file)
        else:
            return guesspath

    for addons_subpath in ADDONS_SUBPATHS:
        if not os.path.exists(j(dest_path, addons_subpath)):
            print("skip subpath '%s'..." % j(dest_path, addons_subpath))
            continue

        for addon in sorted(os.listdir(j(dest_path, addons_subpath))):
            i18n_path = j(dest_path, addons_subpath, addon, 'i18n')
            if not os.path.exists(i18n_path):
                print("skip '%s'..." % i18n_path)
                continue

            print("Processing '%s'... in %s" % (addon, i18n_path))
            if filter_lang:
                suffix = f"{filter_lang}.po"
            else:
                suffix = ".po"

            # for lang in sorted(filter(lambda x: x == 'de.po', os.listdir(i18n_path))):
            for lang in sorted(filter(lambda x: x.endswith(suffix), filter_lang and [suffix] or os.listdir(i18n_path))):

                guess = lambda a, b,: guess_openerp(a, b, addons_subpath, addon)
                src = guess(src_path, lang)
                new = guess(new_path, lang)
                dest = guess(dest_path, lang)
                ref = guess(dest_path, addon+'.pot')

                # language = lang.replace('.po', '')
                # print("   %s: %s (%s) -> %s (%s)" % (language, src, os.path.exists(src), new, os.path.exists(new)))
                if not os.path.exists(src) and os.path.exists(new):
                    subprocess.call(['cp', new, dest])
                elif not os.path.exists(new) and os.path.exists(src):
                    subprocess.call(['cp', src, dest])
                elif not os.path.exists(src) and not os.path.exists(new) and not os.path.exists(dest):
                    subprocess.call(['cp', ref, dest])
                elif os.path.exists(new) and os.path.exists(src):
                # cmd = 'msgcat %(src)s %(new)s -o %(dest)s'
                    cmd = ['msgcat', '--no-wrap', '--use-first', new, src, '-o', dest]
                    # print(" ".join(cmd))
                    subprocess.call(cmd)
                    cmd = ['msgattrib', '--no-wrap', '--translated', '--no-fuzzy', '--no-obsolete', dest, '-o', dest]
                    # print(" ".join(cmd))
                    subprocess.call(cmd)
                cmd = "msgmerge --no-wrap --no-fuzzy-matching -q %(dest)s %(ref)s | msgattrib --no-wrap --no-fuzzy --no-obsolete -o %(dest)s" % {'ref': ref, 'dest': dest}
                # print(cmd)
                subprocess.call(cmd, shell=True)
                # subprocess.call(['msgmerge', dest, ref, '--update', '-N'])

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=True,
                        help='path to source directory where the pot is defined')
    parser.add_argument('--trad', required=True,
                        help='path to reference translations')
    parser.add_argument('--dest', required=True,
                        help='path where generated po will be stored')
    parser.add_argument('--lang', help='optional language to filter')

    args = parser.parse_args()
    if args.lang:
        for lang in args.lang.split(","):
            merge_po(args.ref, args.trad, args.dest, lang)
    else:
        merge_po(args.ref, args.trad, args.dest, args.lang)

