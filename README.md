# Berean

An open source, cross-platform Bible study program

## Table of Contents

* [Getting Started](#getting-started)
* [Developer Guide](#developer-guide)

## Getting Started

Download Crosswire Sword modules as ZIP files from the following links:
* crosswire.org - http://www.crosswire.org/sword/modules/ModDisp.jsp?modType=Bibles
* ebible.org - https://ebible.org/download.php

To import them into Berean, go to `Edit` -> `Preferences` -> `Versions` -> `Add versions`

## Developer Guide

### Bible File Format

The Bible is stored as a nested array using `pickle`:
```python
{...}
```
```python
[
    None,
    [
        [...],
        ...
    ],
    ...
]
```

A metadata object is pickled separately and stored at the top of the file for quick read access.

The first-level array contains Bible books. The 0th-index item is None as a placeholder for the metadata object.

The second-level array contains Bible chapters. The 0th-index item is None, or contains the book colophon if there is one.

The third-level array contains Bible verses. The 0th-index item is None, or contains the chapter subtitle if there is one.

### Index File Format

The index is stored as a dictionary using `pickle`:
```python
{
    'the': '\1\1\1\2\2\2',
    'quick': '\1\2\3'
}
```

For every word that occurs in the Bible, the references of verses that contain it are stored as 3 bytes (e.g., `\1\2\3` = Genesis 2:3).
