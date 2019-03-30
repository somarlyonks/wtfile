# WTFile [![CircleCI](https://img.shields.io/circleci/project/github/somarlyonks/wtfile/master.svg)](https://circleci.com/gh/somarlyonks/wtfile) [![Coveralls branch](https://codecov.io/gh/somarlyonks/wtfile/branch/master/graph/badge.svg)](https://codecov.io/gh/somarlyonks/wtfile)

An insane alternative to `pathlib.Path` and `path.py`.

## requirements

It's just an aggressive and insane option, it deponds on nothing but Python3.6.0+ that supports the powerful "path-like".

## usage

### callable "string"

```python
>>> from wtfile import F
>>> f = F('/home', 'sy')
>>> f
/home/sy
>>> f = f('test.cc')
>>> f
/home/sy/test.cc
>>> f.ext
.cc
>>> f.ext('h')
/home/sy/test.h
>>> f.stem('name')
/home/sy/name.h
>>> f.name
name.h
>>> filepath = os.path.join('/home/sy', f.name)
/home/sy/name.h
```

### operations

```python
>>> f = F('/home/sy') / 'test.cc'
>>> f
/home/sy/test.cc
>>> f.name
test.cc
>>> 'g' + f.ext
.gcc
>>> f.ext + 'g'
.ccg
```

### OO && linkage

```python
>>> f = F('/home/sy', 'test.c')
>>> f.parent
/home/sy
>>> f.parent.children
[]
>>> f.touch()
>>> f.parent.children
['test.c']
>>> f.write('int main(void);').ext('h')
>>> f
/home/sy/test.h
>>> f.read()
'int main(void);'
>>> f.mtime
1553913442.148171
```

For more evil actions you may refer to the [tests.py](./tests.py) or the upcoming docs.

## TODO

- more reliable IO operations
- more tests
- asynchronous support

## references

[PEP 355 -- Path - Object oriented filesystem paths](https://www.python.org/dev/peps/pep-0355/)

[PEP 428 -- The pathlib module -- object-oriented filesystem paths](https://www.python.org/dev/peps/pep-0428/)

[PEP 519 -- Adding a file system path protocol](https://www.python.org/dev/peps/pep-0519/)

## LICENSE

MIT License Copyright (c) 2019 Sy
