#!/usr/bin/env python

import argparse
import os
import subprocess
import re
from datetime import datetime
from os.path import join as j

import polib


REGEX = re.compile(
    "%(\(\w+\)|)([0+-]|)(\d+|\*|)[diouxXcrsa]|%(\(\w+\)|)([0+-]|)(\d+|\*|)(\.(\d+|\*|)|)[eEfFgG]|%%"
)
REGEXWS = re.compile(
    "%(\(\w+\)|)([ #0+-]|)(\d+|\*|)[diouxXcrsa]|%(\(\w+\)|)([ #0+-]|)(\d+|\*|)(\.(\d+|\*|)|)[eEfFgG]|%%"
)
TX_LANGS = [
    "af",
    "am",
    "ar",
    "bg",
    "bs",
    "ca",
    "cs",
    "da",
    "de",
    "el",
    "es",
    "et",
    "eu",
    "fa",
    "fi",
    "fo",
    "fr",
    "gl",
    "gu",
    "he",
    "hr",
    "hu",
    "id",
    "it",
    "ja",
    "ka",
    "kab",
    "ko",
    "lo",
    "lt",
    "lv",
    "mk",
    "mn",
    "nb",
    "ne",
    "nl",
    "pl",
    "pt",
    "pt_BR",
    "ro",
    "ru",
    "sk",
    "sl",
    "sq",
    "sr",
    "sr@latin",
    "sv",
    "sw",
    "th",
    "tr",
    "uk",
    "vi",
    "zh_CN",
    "zh_TW",
]


BADWORD = "NIF"
GOODWORD = "NIT"


def check_parent(path, lang):
    for module in sorted(os.listdir(path)):
        # if not module.endswith("sign"):
        #     continue
        i18n_path = j(path, module, "i18n")
        if not os.path.exists(i18n_path):
            # print("skip '%s'..." % i18n_path)
            continue

        target_path = j(i18n_path, lang + ".po")
        parent_path = j(i18n_path, lang.split("_")[0] + ".po")
        pot_path = j(i18n_path, module + ".pot")

        if not os.path.exists(target_path):
            print(f"skip {target_path}, does not exist")
            continue
        if not os.path.exists(parent_path):
            print(f"skip {parent_path}, does not exist")
            continue
        if not os.path.exists(pot_path):
            print(f"skip {pot_path}, does not exist")
            continue

        parent = polib.pofile(parent_path)
        pot = polib.pofile(pot_path)

        if os.path.exists(target_path):
            child = polib.pofile(target_path, wrapwidth=78)
        else:
            child = polib.POFile(wrapwidth=78)
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M+0000")
            child.metadata = pot.metadata
            child.metadata["Language"] = lang
            child.metadata["PO-Revision-Date"]: now

        child.merge(pot)
        parent.merge(pot)

        for entry in child:
            if not entry.translated():
                continue
            parent_entry = parent.find(entry.msgid, by="msgid")
            if not parent_entry:
                # not present in parent, outdated
                entry.obsolete = True
            if not parent_entry.translated():
                # keep
                continue
            if entry.msgstr.lower() == parent_entry.msgstr.lower():
                # both are translated the same, remove child
                entry.obsolete = True

        # for entry in parent:
        #     child_entry = child.find(entry.msgid, by="msgid", msgctxt=entry.msgctxt)
        #     if not child_entry:
        #         # entry present in parent but not in child, nothing to do
        #         continue
        #         # child_entry = polib.POEntry(
        #         #     msgid=entry.msgid,
        #         # )
        #         # child_entry.comment = entry.comment
        #         # child_entry.occurrences = entry.occurrences
        #         # child.append(child_entry)

        #     if not child_entry.translated():
        #         # child and parent both not translated, remove child
        #         child_entry.obsolete = True
        #         continue

        #     if entry.msgstr == child_entry.msgstr:
        #         # both are translated the same, remove child
        #         child_entry.obsolete = True

        print(f"Writting changes to {target_path}")
        child.save(target_path)
        cmd = f"msgattrib {target_path} --no-fuzzy --no-obsolete -o {target_path}"
        subprocess.call(cmd, shell=True)

def _verify_placeholder(letter, entry, po_path):
    expected = f"%{letter}"
    rfrom, rto = None, None
    if expected in entry.msgid and expected not in entry.msgstr:

        if f"% {letter}" in entry.msgstr:
            if f" %{letter}" in entry.msgid:
                if f" % {letter}" in entry.msgstr:
                    rfrom, rto = f" % {letter}", f" %{letter}"
                else:
                    rfrom, rto = f"% {letter}", f" %{letter}"
            elif f"%{letter} " in entry.msgid:
                rfrom, rto = f"% {letter}", f"%{letter} "
            else:
                rfrom, rto = f"% {letter}", expected
        elif f"%{letter.upper()}" in entry.msgstr:
            rfrom = f"%{letter.upper()}"
        elif f"{letter.upper()}%" in entry.msgstr:
            rfrom = f"{letter.upper()}%"
        elif f"{letter}%" in entry.msgstr:
            rfrom = f"{letter}%"
        elif "%" in entry.msgstr:
            rfrom = "%"
            rto = expected
        elif entry.msgid.startswith(expected):
            rfrom = entry.msgstr
            rto = f"%{letter} {rfrom}"
        elif entry.msgid.endswith(expected):
            rfrom = entry.msgstr
            rto = f"{rfrom} %{letter}"
        else:
            print(
                f"Bad translation in {po_path} :\n\t{entry.msgid}"
            )
            rfrom = entry.msgstr
            rto = ""
    return rfrom, rto

def check_po_percent(path):
    for addon in sorted(os.listdir(path)):
        i18n_path = j(path, addon, "i18n")
        if not os.path.exists(i18n_path):
            print("skip '%s'..." % i18n_path)
            continue
        # print("Processing '%s'... in %s" % (addon, i18n_path))
        for lang in sorted(filter(lambda x: x.endswith(".po"), os.listdir(i18n_path))):
            language = lang.replace(".po", "")

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
                    rfrom, rto = "\\n", "\n"

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

                        for letter in ["s", "d", "r"]:
                            rfrom, rto = _verify_placeholder(letter, entry, po_path)
                            if rfrom:
                                break

                if rfrom:
                    entry.msgstr = entry.msgstr.replace(rfrom, rto)
                    save = True

            if save:
                po.save()


TO_MATCH = ["&amp;times;", "&times;", "<span>&amp;times;</span>"]

def check_html_escape(path, filter_lang):
    for module in sorted(os.listdir(path)):
        i18n_path = j(path, module, "i18n")
        if not os.path.exists(i18n_path):
            continue

        for lang in sorted(
            filter(
                lambda x: x.endswith(".po")
                and (x.startswith(filter_lang) if filter_lang else True),
                os.listdir(i18n_path),
            )
        ):
            target_path = j(i18n_path, lang)
            po = polib.pofile(target_path, wrapwidth=78)
            save = False
            for entry in po:
                if entry.msgstr:
                    
                    for expr in TO_MATCH:
                        if expr in entry.msgid and expr not in entry.msgstr:
                            if entry.msgid == expr:
                                entry.msgstr = expr
                                save = True
                                break
                            print(
                                f"Bad translation in {target_path} :\n\t{entry.msgid[:30]}"
                            )
                            break
            if save:
                po.save()

def check_src_equal_trans(path, filter_lang):
    for module in sorted(os.listdir(path)):
        i18n_path = j(path, module, "i18n")
        if not os.path.exists(i18n_path):
            continue

        for lang in sorted(
            filter(
                lambda x: x.endswith(".po")
                and (x.startswith(filter_lang) if filter_lang else True),
                os.listdir(i18n_path),
            )
        ):
            target_path = j(i18n_path, lang)
            po = polib.pofile(target_path, wrapwidth=78)
            save = False
            for entry in po:
                if entry.msgstr and entry.msgid == entry.msgstr:
                    entry.msgstr = ""
                    save = True
                    print(
                        f"Bad translation in {target_path} :\n\t{entry.msgid[:30]}"
                    )
            if save:
                po.save()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--trad", required=True, help="path to reference translations")
    parser.add_argument("--lang", help="language to sanitize")

    args = parser.parse_args()
    # check_po_percent(args.trad)
    for lang in args.lang.split(','):
        check_parent(args.trad, lang)
    # check_html_escape(args.trad, args.lang)
    # check_src_equal_trans(args.trad, args.lang)
