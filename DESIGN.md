## Sword Modules

Berean has its own format for storing Bibles as detailed below, but can import Bibles provided by the Sword project at [Crosswire.org](https://www.crosswire.org/sword/modules/ModDisp.jsp?modType=Bibles).

It can also automatically download and import Bible modules from the FTP repositories listed on the [the Crosswire wiki](https://wiki.crosswire.org/Official_and_Affiliated_Module_Repositories). 

## Bible File Structure

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

## Index File Structure

The index is stored as a dictionary using `pickle`:
```python
{
    'the': '\1\1\1\2\2\2',
    'quick': '\1\2\3'
}
```

For every word that occurs in the Bible, the references of verses that contain it are stored as 3 bytes (e.g., `\1\2\3` = Genesis 2:3).
