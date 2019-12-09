#!/usr/bin/env python

import argparse
import os
import polib
import re
from os.path import join as j


REGEX = re.compile("%(\(\w+\)|)([0+-]|)(\d+|\*|)[diouxXcrsa]|%(\(\w+\)|)([0+-]|)(\d+|\*|)(\.(\d+|\*|)|)[eEfFgG]|%%")
REGEXWS = re.compile("%(\(\w+\)|)([ #0+-]|)(\d+|\*|)[diouxXcrsa]|%(\(\w+\)|)([ #0+-]|)(\d+|\*|)(\.(\d+|\*|)|)[eEfFgG]|%%")
TX_LANGS = ['af', 'am', 'ar', 'bg', 'bs', 'ca', 'cs', 'da', 'de', 'el', 'es', 'et', 'eu', 'fa', 'fi', 'fo', 'fr', 'gl', 'gu', 'he', 'hr', 'hu', 'id', 'it', 'ja', 'ka', 'kab', 'ko', 'lo', 'lt', 'lv', 'mk', 'mn', 'nb', 'ne', 'nl', 'pl', 'pt', 'pt_BR', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'sr@latin', 'sv', 'sw', 'th', 'tr', 'uk', 'vi', 'zh_CN', 'zh_TW']


def check_po_percent(path):
    for addon in sorted(os.listdir(path)):
        i18n_path = j(path, addon, 'i18n')
        if not os.path.exists(i18n_path):
            print("skip '%s'..." % i18n_path)
            continue
        print("Processing '%s'... in %s" % (addon, i18n_path))
        for lang in sorted(filter(lambda x: x.endswith('.po'), os.listdir(i18n_path))):
            language = lang.replace('.po', '')

            # if len(language.split('_')) > 1 and language not in ['zh_CN', 'pt_BR', 'zh_TW']:
            # if language in TX_LANGS:
            #     # clean only main translations
            #     continue

            # if language != 'tr':
            #     continue

            po_path = j(i18n_path, lang)
            po = polib.pofile(po_path, wrapwidth=78)
            save = False
            for entry in po:
                rfrom, rto = False, False
                if entry.msgstr and "\\n" in entry.msgstr:
                    # assert: Translation terms may not include escaped newlines
                    rfrom, rto = '\\n', '\n'

                placeholders_src = sorted([m.group(0) for m in REGEX.finditer(entry.msgid)])
                placeholders_trans = sorted([m.group(0) for m in REGEX.finditer(entry.msgstr)])
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

                        if '%s' in entry.msgid and '%s' not in entry.msgstr:

                            if '% s' in entry.msgstr:
                                if ' %s' in entry.msgid:
                                    rfrom, rto = '% s', ' %s'
                                elif '%s ' in entry.msgid:
                                    rfrom, rto = '% s', '%s '
                                else:
                                    rfrom, rto = '% s', '%s'
                            elif '%S' in entry.msgstr:
                                rfrom = '%S'
                            elif 'S%' in entry.msgstr:
                                rfrom = 'S%'
                            elif 's%' in entry.msgstr:
                                rfrom = 's%'
                            elif '%s' in entry.msgid and '%' in entry.msgstr:
                                rfrom = '%'
                                rto = '%s'
                            elif entry.msgid.startswith('%s'):
                                rfrom = entry.msgstr
                                rto = '%s '+rfrom
                            elif entry.msgid.endswith('%s'):
                                rfrom = entry.msgstr
                                rto = rfrom + ' %s'
                            else:
                                print(f"Bad translation in {po_path} :\n\t{entry.msgid}")

                if rfrom:
                    entry.msgstr = entry.msgstr.replace(rfrom, rto or '%s')
                    save = True

            if save:
                po.save()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--trad', required=True,
                        help='path to reference translations')

    args = parser.parse_args()
    check_po_percent(args.trad)
