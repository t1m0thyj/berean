import os
import pickle
import sys
from collections.abc import Sequence
from html.parser import HTMLParser
from itertools import chain

from pysword.modules import SwordModules


def get_books(bible):
    return list(chain(*bible.get_structure().get_books().values()))


def tag_matches(subset, superset):
    for tag_sub in subset:
        if tag_sub in superset or any(tag_super.startswith(f"{tag_sub}:") for tag_super in superset):
            return True
    return False


class Bible(Sequence):
    def __init__(self, filename):
        super().__init__()
        modules = SwordModules(filename)
        found_modules = modules.parse_modules()
        self._bible = modules.get_bible_from_module(list(found_modules.keys())[0])
        self._title = found_modules[list(found_modules.keys())[0]]["description"]

    def __getitem__(self, i):
        if i == 0:
            return self._title
        else:
            return Book(self._bible, i)

    def __len__(self):
        return len(get_books(self._bible)) + 1


class Book(Sequence):
    def __init__(self, bible, book):
        super().__init__()
        self._bible = bible
        self._book = book

    def __getitem__(self, i):
        if i == 0:
            return get_books(self._bible)[self._book - 1].name
        else:
            return Chapter(self._bible, self._book, i)

    def __len__(self):
        return get_books(self._bible)[self._book - 1].num_chapters + 1


class Chapter(Sequence):
    def __init__(self, bible, book, chapter):
        super().__init__()
        self._bible = bible
        self._book = book
        self._chapter = chapter
        self._verses = None

    def __getitem__(self, i):
        if i == 0:
            return Title(self._bible.get(get_books(self._bible)[self._book - 1].name, self._chapter, 1, False))
        else:
            return Verse(self._bible.get(get_books(self._bible)[self._book - 1].name, self._chapter, i, False))

    def __len__(self):
        return get_books(self._bible)[self._book - 1].chapter_lengths[self._chapter - 1] + 1


class Title(str):
    def __new__(cls, data):
        return str.__new__(cls, VerseParser(data, include_tags=["title:psalm"]))


class Verse(str):
    def __new__(cls, data):
        return str.__new__(cls, VerseParser(data, exclude_tags=["note", "title:psalm"]))


class VerseParser(HTMLParser):
    def __init__(self, data, exclude_tags=None, include_tags=None):
        super().__init__()
        self._data = data
        self._exclude_tags = exclude_tags or []
        self._include_tags = include_tags or []
        self._output = None
        self._tags = []

    def __str__(self):
        if self._output is None:
            self.feed(self._data)
        return self._output or ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self._tags.append(tag if attrs.get("type") is None else f"{tag}:{attrs['type']}")
        if tag == "milestone" and "marker" in attrs:
            self._output = ("" if self._output is None else f"{self._output} ") + attrs["marker"] + " "

    def handle_endtag(self, tag):
        self._tags = [t for t in self._tags if t != tag and not t.startswith(f"{tag}:")]

    def handle_data(self, data):
        if self._include_tags and not tag_matches(self._include_tags, self._tags):
            return
        elif self._exclude_tags and not self._include_tags and tag_matches(self._exclude_tags, self._tags):
            return
        if "divinename" in self._tags:
            data = data.upper()
        if "transchange:added" in self._tags:
            data = f"[{data}]"
        self._output = (self._output or "") + data


if __name__ == "__main__":
    bible = Bible(sys.argv[1])
    print(bible[0])
    bible2 = [bible[0]]
    for b in range(1, len(bible)):
        print(bible[b][0])
        bible2.append([bible[b][0]])
        for c in range(1, len(bible[b])):
            bible2[b].append([str(bible[b][c][0]) or None])
            for v in range(1, len(bible[b][c])):
                bible2[b][c].append(str(bible[b][c][v]).strip())
    with open(os.path.splitext(sys.argv[1])[0] + ".bbl", 'wb') as fileobj:
        pickle.dump(bible2, fileobj)
