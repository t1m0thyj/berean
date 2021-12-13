import os.path
import pickle
import re
import shutil

import wx

import sword
from constants import BOOK_NAMES

_ = wx.GetTranslation


def download_version(version_data, repo, out_dir):
    version_name = version_data["abbreviation"]
    dialog = wx.ProgressDialog(_("Importing %s") % version_name, _("Downloading..."), 100)
    temp_dir = repo.download_module(version_data, lambda percent: dialog.Update(percent * 30))
    dialog.Update(30)
    sword.convert_bible(temp_dir, os.path.join(out_dir, version_name + ".bbl"),
                        lambda idx: dialog.Update(idx + 31, (_("Processing %s...") % BOOK_NAMES[idx - 1])) if idx <= len(BOOK_NAMES) else _("Saving Bible..."))
    shutil.rmtree(temp_dir)
    dialog.Update(100)
    dialog.Destroy()


def import_version(in_file, out_dir):
    version_name = os.path.splitext(os.path.basename(in_file))[0]
    dialog = wx.ProgressDialog(_("Importing %s") % version_name, "", 70)
    sword.convert_bible(in_file, os.path.join(out_dir, version_name + ".bbl"),
                        lambda idx: dialog.Update(idx + 1, (_("Processing %s...") % BOOK_NAMES[idx - 1])) if idx <= len(BOOK_NAMES) else _("Saving Bible..."))
    dialog.Update(70)
    dialog.Destroy()


def index_version(version, Bible, index_dir):
    dialog = wx.ProgressDialog(_("Indexing %s") % version, "", 68)
    index = {}
    for b in range(1, len(Bible)):
        dialog.Update(b - 1, _("Processing %s...") % BOOK_NAMES[b - 1])
        if not Bible[b]:
            continue
        for c in range(1, len(Bible[b])):
            if not Bible[b][c]:
                continue
            for v in range(1, len(Bible[b][c])):
                if not Bible[b][c][v]:
                    continue
                verse = re.sub(r"[^\w\s'\-]", r"", Bible[b][c][v].replace("--", " "),
                               flags=re.UNICODE)
                for word in set(verse.split()):  # Remove duplicates
                    index.setdefault(word, []).extend([chr(i) for i in (b, c, v)])
    dialog.Update(66, _("Saving index..."))
    for word in index:
        index[word] = "".join(index[word])
    with open(os.path.join(index_dir, "%s.idx" % version), 'wb') as fileobj:
        pickle.dump(index, fileobj, -1)
    dialog.Update(68)
    dialog.Destroy()
    return index
