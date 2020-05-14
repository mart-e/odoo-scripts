#!/usr/bin/env python

from pathlib import Path
import opencc
import polib

converter = opencc.OpenCC('s2t.json')
for filepath in Path('.').glob("*/zh_CN.po"):
    pofile = polib.pofile(str(filepath))
    outpath = filepath.parent / "zh_TW.po"
    for entry in pofile:
        if entry.msgstr:
            entry.msgstr = converter.convert(entry.msgstr)

    pofile.metadata["Language"] = "zh_TW"
    pofile.metadata["Language-Team"] = "Generated via OpenCC from zh_CN"
    pofile.save(fpath=str(outpath))
