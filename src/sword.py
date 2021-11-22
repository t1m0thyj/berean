import configparser
import ftplib
import hashlib
import os
import pickle
import sys
import tarfile
import tempfile
import urllib.request
from collections.abc import Sequence
from html.parser import HTMLParser
from itertools import chain

from pysword.modules import SwordModules

from constants import BOOK_NAMES


def osis2bbl(osis_bible, progress_callback):
    bbl_bible = [osis_bible[0]]
    for b in range(1, len(osis_bible)):
        progress_callback(b)
        bbl_bible.append([str(osis_bible[b][0]) or None])
        for c in range(1, len(osis_bible[b])):
            bbl_bible[b].append([str(osis_bible[b][c][0]) or None])
            for v in range(1, len(osis_bible[b][c])):
                bbl_bible[b][c].append(str(osis_bible[b][c][v]).strip())
    return bbl_bible


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
        self._metadata = found_modules[list(found_modules.keys())[0]]

    def __getitem__(self, i):
        if i == 0:
            return self._metadata
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
            return str(ColophonParser(self._bible, get_books(self._bible)[self._book - 1]))
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
            return Subtitle(self._bible.get(get_books(self._bible)[self._book - 1].name, self._chapter, 1, False))
        else:
            return Verse(self._bible.get(get_books(self._bible)[self._book - 1].name, self._chapter, i, False))

    def __len__(self):
        return get_books(self._bible)[self._book - 1].chapter_lengths[self._chapter - 1] + 1


class Subtitle(str):
    def __new__(cls, data):
        return str.__new__(cls, VerseParser(data, include_tags=["title:psalm"]))


class Verse(str):
    def __new__(cls, data):
        return str.__new__(cls, VerseParser(data, exclude_tags=["note", "title"]))


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


class ColophonParser(VerseParser):
    def __init__(self, bible, book_info):
        super().__init__(bible.get(book_info.name, book_info.num_chapters,
                                   book_info.chapter_lengths[book_info.num_chapters - 1], False))
        self._read = False

    def handle_starttag(self, tag, attrs):
        VerseParser.handle_starttag(self, tag, attrs)
        if tag == "div" and dict(attrs).get("type") == "colophon":
            self._read = not self._read

    def handle_data(self, data):
        if self._read:
            VerseParser.handle_data(self, data)


def get_master_repo_list():
    config = configparser.ConfigParser(strict=False)
    with urllib.request.urlopen("https://crosswire.org/ftpmirror/pub/sword/masterRepoList.conf") as fileobj:
        config.read_string(fileobj.read().decode())
    return [v.removeprefix("FTPSource=") for k, v in config.items("Repos")]


class BibleRepository:
    def __init__(self, repo_info, cache_dir):
        self.repo_info = repo_info
        self.cache_dir = cache_dir
        repo_name, ftp_host, ftp_path = repo_info.split("|")
        self.repo_name = repo_name
        self.ftp_host = ftp_host
        self.ftp_path = ftp_path

    @property
    def repo_id(self):
        return hashlib.md5(f"{self.ftp_host}{self.ftp_path}".encode()).hexdigest()

    def get_version_data(self, busy_callback=None, use_cache=True):
        cache_path = os.path.join(self.cache_dir, f"{self.repo_id}.tgz")
        if not use_cache or not os.path.isfile(cache_path):
            if busy_callback:
                wait = busy_callback()
            urllib.request.urlretrieve(f"ftp://{self.ftp_host}{self.ftp_path}/mods.d.tar.gz", cache_path)
            if busy_callback:
                del wait

        tgz = tarfile.open(cache_path, "r:gz")
        version_data = []
        for member in tgz.getmembers():
            if not member.isfile() or not member.name.endswith(".conf"):
                continue
            config = configparser.ConfigParser(strict=False)
            try:
                config.read_string(tgz.extractfile(member).read().decode())
            except configparser.ParsingError:
                pass
            root_section = config.sections()[0]
            if config[root_section]["ModDrv"].lower() == "ztext":
                version_data.append({
                    "abbreviation": config[root_section].get("Abbreviation", root_section),
                    "description": config[root_section]["Description"],
                    "ftpPath": config[root_section]["DataPath"].removeprefix("./"),
                    "ftpUrl": self.ftp_host + self.ftp_path,
                    "tgzPath": member.name
                })
        return sorted(version_data, key=lambda data: data["abbreviation"])

    def download_module(self, version_data, progress_callback):
        ftp_host, ftp_base_path = version_data["ftpUrl"].split("/", 1)
        with ftplib.FTP() as ftp:
            ftp.connect(ftp_host)
            ftp.login()
            ftp_paths = ftp.nlst(ftp_base_path + "/" + version_data["ftpPath"])

        temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(temp_dir, version_data["ftpPath"]))
        for i, ftp_path in enumerate(ftp_paths):
            progress_callback((i + 1) / (len(ftp_paths) + 1))
            urllib.request.urlretrieve(f"ftp://{ftp_host}/{ftp_path}",
                                       os.path.join(temp_dir, version_data["ftpPath"], os.path.basename(ftp_path)))

        tgz = tarfile.open(os.path.join(self.cache_dir, f"{self.repo_id}.tgz"), "r:gz")
        tgz.extract(version_data["tgzPath"], temp_dir)
        return temp_dir


if __name__ == "__main__":
    sword_bible = Bible(sys.argv[1])
    ber_bible = osis2bbl(sword_bible, lambda idx: print(BOOK_NAMES[idx - 1]))
    with open(os.path.splitext(sys.argv[1])[0] + ".bbl", 'wb') as fileobj:
        pickle.dump(ber_bible[0], fileobj)
        ber_bible[0] = None
        pickle.dump(ber_bible, fileobj)
