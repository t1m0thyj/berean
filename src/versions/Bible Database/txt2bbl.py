import cPickle
import re
import sys

version = sys.argv[1]
if len(sys.argv) == 2:
    filename = "b_%s.txt" % version.lower()
else:
    filename = "b_%s.txt" % sys.argv[2].lower()
with open(filename, 'r') as fileobj:
    lines = [line.rstrip("\r\n") for line in fileobj]
Bible = [unicode(version)]
if version == "Weymouth":
    for b in range(1, 40):
        Bible.append(tuple())
for line in lines:
    match = re.match(r"\d+\s+(\d+)\s+(\d+)\s+(\d+)\s+(.*)", line)
    if not match:
        break
    book, chapter, verse, text = match.groups()
    if text == "[]" or not text:
        continue
    book, chapter, verse = int(book), int(chapter), int(verse)
    if chapter == 1 and verse == 1:
        Bible.append([None])
    if len(Bible[book]) == chapter:
        Bible[book].append([None])
        if book == 19:
            if version != "DutSVV":
                match = re.match(r"(?:&lt;|{|\(\d+:\d+\) |<<|\()(.+?)(?:&gt;|}"
                                 "| \(\d+:\d+\)|>>|\)) ", text)
            else:
                match = re.match(r"(.+?) \(\d+:\d+\) ", text)
            if match:
                Bible[book][chapter][0] = unicode(match.group(1).
                                                  decode("latin_1")).strip()
                text = text[match.end():]
    if version == "DutSVV" or version == "FreSegond" or version == "JPS":
        text = re.sub(r"\(\d+:\d+\) ", r"", text)
    if version == "BBE" or version == "SpaRV":
        text = text.replace("(Selah.)", "Selah.")
    elif version == "Darby":
        text = text.replace("*", "")
    elif version == "FreSegond":
        text = text.replace(" -", " ")
    elif version == "GerLut1545":
        text = text.replace("(Sela.)", "Sela.")
    elif version == "JPS":
        text = re.sub(r" ,(?=\w)", r", ", text)
    elif version == "SpaSEV":
        text = text.lstrip("\xb6").replace("<I>", "[").replace("</I>", "]"). \
            replace("  ", " ").replace(" ,", ",")
    elif version == "Webster":
        text = re.sub(r"\\\d+:\d+\\", r"", text, 1).rstrip("\\")
    elif version == "Weymouth":
        text = text.replace("<", "").replace(">", "")
    elif version == "YLT":
        text = re.sub(r"`([a-z]+(\W? [a-z]+)?)'", r"[\1]", text,
                      flags=re.IGNORECASE)
        text = re.sub(r"'(?!s\b)", "\x92", text.replace("`", "\x91"))
    text = re.sub(r"\s*--\s*", r"--", text)
    Bible[book][chapter]. \
        append(unicode(re.sub(r"\s(?=(\s|[!),.:;?]))|(?<=\[)\s", r"", text).
                       decode("latin_1")).strip())
if version == "JPS":
    for b in range(40, 67):
        Bible.append(tuple())
for b in range(1, 67):
    if Bible[b] == tuple():
        continue
    for c in range(1, len(Bible[b])):
        Bible[b][c] = tuple(Bible[b][c])
    Bible[b] = tuple(Bible[b])
with open("%s.bbl" % version, 'wb') as fileobj:
    cPickle.dump(tuple(Bible), fileobj, -1)
