from functools import partial
import fnmatch
import glob
import os
import re
import stat
import shutil as sh
import sys


VERBOSE = False

__print = print  # pylint: disable=invalid-name


def print(*_, **__):
    verbose = __.pop('verbose', True)
    if VERBOSE or verbose:
        __print(*_, **__)


def TODO(*_):
    scan = False
    if os.getenv('CI'):
        pass
    elif scan:
        raise NotImplementedError(*_)

# chores
# **************************************************************************


__all__ = ['F']
__author__ = 'Sy<somarl@live.com>'
__doc__ = """
An aggressive alternative to pathlib.path and path.py which supports

>>> f = F('/home/sy', 'test.cc')
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

Q&A

Q: How do I know whether a specific action does IO operation or not?
A: If it's an action adaptable to both path/io, it depends on a parameter
   called 'dry' which is False on default. Otherwise it just manipulates
   the path string.

Q: Exceptions?
A: There is no extra exception introduced, all operations are ported to module
   os or module os.path, wtfile itself is not supposed to corrupt.
   If the error message is in Chinese, it's raised by wtfile, otherwise it
   is supposed to be raised by python module(if not, fire an issue).
"""


LINESEP = os.linesep
LINESEPS = ['\r\n', '\r', '\n']
LINESEPS_U = LINESEPS + ['\u0085', '\u2028', '\u2029']
P_NEWLINE = re.compile('|'.join(LINESEPS))
P_NEWLINE_U = re.compile('|'.join(LINESEPS_U))
P_NEWLINE_END = re.compile(r'(?:{0})$'.format(P_NEWLINE.pattern))
P_NEWLINE_END_U = re.compile(r'(?:{0})$'.format(P_NEWLINE_U.pattern))


class classproperty(property):  # pylint: disable=invalid-name

    def __get__(self, cls, owner):
        return self.fget(owner)

    def __set__(self, *_):
        raise AttributeError("Read only classproperty")


class FMeta(type):

    pass


class FBase(str, metaclass=FMeta):

    module = os.path

    def __new__(cls, *_, **__):
        print('__new__', _, __, verbose=False)
        if _:
            return super(FBase, cls).__new__(cls, cls.module.join(*_))
        return super(FBase, cls).__new__(cls, cls.module.join(''))

    def __init__(self, *_, mode='t', parent=None):  # pylint: disable=super-init-not-called
        self._parent = parent
        self._mode = mode  # 't'/'b'
        self.__bwd = None

    def _derive_(self, *_):
        return type(self)(*_, mode=self._mode, parent=self._parent)

    def __add__(self, other):
        return self._derive_(str.__add__(self, other))

    def __radd__(self, other):
        return self._derive_(other.__add__(self))

    def __call__(self):
        raise NotImplementedError()

    def __repr__(self):
        if VERBOSE:
            return f'{type(self).__name__}({super(FBase, self).__repr__()})'
        return f'{super(FBase, self).__repr__()}'

    def to_str(self):
        return str(self)


class FPath(FBase):

    def __div__(self, rest):
        return self._derive_(self, rest)

    __truediv__ = __div__

    def __rdiv__(self, rest):
        return self._derive_(rest, self)

    __rtruediv__ = __rdiv__

    def __fspath__(self):
        """PEP519"""
        return self

    # deprecated
    # realpath(misleading, implicit api)
    # commonpath
    # commonprefix
    # lexists

    @property
    def parent(self):
        """Return the directory name of pathname path.
        This is the first element of the pair returned by passing path to the
        function split() and proxied by F.
        """
        return self._derive_(self.module.dirname(self))

    @property
    def name(self):
        """Return the directory name of pathname path.
        This is the second element of the pair returned by passing path to the
        function split() and proxied by FName.
        """
        return FName(self.module.basename(self), parent=self)

    # @name.setter
    # def name(self, value):
    #     """deparecated"""
    #     self.name(value)

    @property
    def stem(self):
        stem = self.name.replace(self.ext, '')
        return FStem(stem, parent=self)

    # @stem.setter
    # def stem(self, value):
    #     """deparecated"""
    #     self.stem(value)

    @property
    def ext(self):
        ext = self.module.splitext(self)[1]
        return FExt(ext, parent=self)

    # @ext.setter
    # def ext(self, value):
    #     """deparecated"""
    #     self.ext(value)

    def cd(self, target):
        """cd relative path with dry path
        Different from os.path.join, supports relative path like cd('..'), cd
        ('../sy') and specially cd('...').
        Different from with FIO block, it doesn't really do IO chdir, you can
        do it like
        ```python
        with F.DIR.cd('../Colors') as folder:
            pass
        ```
        """
        if target == '...':
            return self.parent.parent
        return self._derive_(self, target).norm()

    def norm(self):
        """Normalize by collapsing redundant separators and up-level
        references so that A//B, A/B/, A/./B and A/foo/../B all become A/B.
        This string manipulation may change the meaning of a path that
        contains symbolic links.
        """
        return self._derive_(self.module.normpath(self))

    normal = norm

    # def normcase(self):
    #     """deprecated(window only)"""
    #     return self._derive_(self.module.normcase(self))

    def match(self, pattern):
        """Test whether the filename string matches the pattern string,
        returning True or False.
        If the operating system is case-insensitive, will be normalized to all
        lower- or upper-case before the comparison is performed. fnmatchcase()
        can be used to perform a case-sensitive comparison, regardless of
        whether that’s standard for the operating system.
        """
        return fnmatch.fnmatch(self, pattern)

    def matchcase(self, pattern):
        return fnmatch.fnmatchcase(self, pattern)


class FIO(FBase):

    def __enter__(self):
        """cd dir
        with F('/home', 'user') as cwd:
            print(F().cwd)
        """
        self.__bwd = self.cwd
        os.chdir(self)
        return self

    def __exit__(self, *_):
        try:
            bwd = self.__bwd
            del self.__bwd
            os.chdir(bwd)
        except AttributeError:
            raise TypeError('我来到你的城市，走过你来时的路。')

    def __iter__(self):
        """ different to for child in f.children, it joins the paths """
        if not self.isdir():
            yield from self.read().split('\n')
        else:
            for child in self.children:
                yield self._derive_(self, child)

    @property
    def cwd(self):
        return self._derive_(os.getcwd())

    @property
    def abspath(self):
        """Return a normalized absolutized version of the pathname path.
        On most platforms, this is equivalent to calling the function
        normpath() as follows: normpath(join(os.getcwd(), path)).
        """
        return self._derive_(self.module.abspath(self))

    @property
    def children(self):
        return os.listdir(self)

    @property
    def siblings(self):
        return [file for file in self.parent.children if file != self.name]

    @property
    def content(self):
        if self.isdir():
            return self.children
        return self.read()

    @property
    def root(self):
        TODO()

    # @property
    # def drive(self):
    #     """deprecated(windows only)"""
    #     return self._derive_(self.module.splitdrive(self))

    def glob(self, pathname, *, relative=False, recursive=False):
        if relative:
            pathname = self.cd(pathname)
        return list(map(type(self), glob.glob(pathname, recursive=recursive)))

    def iglob(self, pathname, *, relative=False, recursive=False):
        if relative:
            pathname = self.cd(pathname)
        yield from map(type(self), glob.iglob(pathname, recursive=recursive))

    def exists(self):
        return self.module.exists(self)

    def isabs(self):
        """Return True if path is an absolute pathname.
        On Unix, that means it begins with a slash, on Windows that it begins
        with a (back)slash after chopping off a potential drive letter.
        """
        return self.module.isabs(self)

    def isfile(self):
        """Return True if path is an existing regular file.
        This follows symbolic links, so both islink() and isfile() can be true
        for the same path.
        """
        return self.module.isfile(self)

    def isdir(self):
        """Return True if path is an existing directory.
        This follows symbolic links, so both islink() and isdir() can be true
        for the same path.
        """
        return self.module.isdir(self)

    def islink(self):
        """Return True if path refers to an existing directory entry that is a
        symbolic link. Always False if symbolic links are not supported by the
        Python runtime.
        """
        return self.module.islink(self)

    def ismount(self):
        """Return True if pathname path is a mount point: a point in a file
        system where a different file system has been mounted. On POSIX, the
        function checks whether path’s parent, path/.., is on a different
        device than path, or whether path/.. and path point to the same i-node
        on the same device — this should detect mount points for all Unix and
        POSIX variants. It is not able to reliably detect bind mounts on the
        same filesystem. On Windows, a drive letter root and a share UNC are
        always mount points, and for any other path GetVolumePathName is
        called to see if it is different from the input path.
        """
        return self.module.ismount(self)

    def mkdir(self, dirname=None, mode=0o777):
        """Create a directory named path with numeric mode mode.
        If the directory already exists, FileExistsError is raised.
        On some systems, mode is ignored. Where it is used, the current umask
        value is first masked out. If bits other than the last 9 (i.e. the
        last 3 digits of the octal representation of the mode) are set, their
        meaning is platform-dependent. On some platforms, they are ignored
        and you should call chmod() explicitly to set them.

        This function can also support paths relative to directory
        descriptors.
        """
        path = self if not dirname else self / dirname
        os.mkdir(path, mode)
        return self._derive_(path)

    def mkfile(self, filename=None, mode=0o600):
        path = self if not filename else self / filename
        os.mknod(path, mode)
        return self._derive_(path)

    # alias
    mknod = mkfile
    touch = mkfile

    def rm(self, f=False):  # pylint: disable=invalid-name
        if self.isdir():
            def onerror(_, path, __):
                if f:
                    os.chmod(path, stat.S_IWRITE)
                    os.rmdir(path)
            sh.rmtree(self, onerror=onerror)
        elif self.isfile():
            os.remove(self)
        else:
            raise TypeError("此情无计可消除，才下眉头，却上心头。")

    def clear(self, target=None, f=False):
        """Remove a file/dir and recreate it.
        """
        path = self if not target else self.cd(target)
        if path.isfile():
            path.rm(f)
            return path.mkfile()
        if path.exists():
            path.rm(f)
        return path.mkdir()

    @property
    def size(self):
        return self.getSize(deep=False)

    def getSize(self, inode=False, deep=True):
        if inode or self.isfile():
            return self.module.getsize(self)

        size = 0
        for child in self:
            if child.isfile():
                size += self.module.getsize(child)
            elif deep:
                size += child.getSize()
        return size

    @property
    def atime(self):
        """Return the time of last access of path.
        The return value is a floating point number giving the number of
        seconds since the epoch (see the time module). Raise OSError if the
        file does not exist or is inaccessible.
        """
        return self.module.getatime(self)

    @property
    def mtime(self):
        """Return the time of last modification of path.
        The return value is a floating point number giving the number of
        seconds since the epoch (see the time module). Raise OSError if the
        file does not exist or is inaccessible.
        """
        return self.module.getmtime(self)

    @property
    def ctime(self):
        """Return the system’s ctime which, on some systems (like Unix) is the
        time of the last metadata change, and, on others (like Windows), is
        the creation time for path. The return value is a number giving the
        number of seconds since the epoch (see the time module). Raise OSError
        if the file does not exist or is inaccessible.
        """
        return self.module.getctime(self)

    def expanduser(self):
        """On Unix and Windows, return the argument with an initial component
        of ~ or ~user replaced by that user’s home directory.
        On Unix, an initial ~ is replaced by the environment variable HOME if
        it is set; otherwise the current user’s home directory is looked up in
        the password directory through the built-in module pwd.
        An initial ~user is looked up directly in the password directory.
        On Windows, HOME and USERPROFILE will be used if set, otherwise a
        combination of HOMEPATH and HOMEDRIVE will be used. An initial ~user
        is handled by stripping the last directory component from the created
        user path derived above.
        If the expansion fails or if the path does not begin with a tilde, the
        path is returned unchanged.
        """
        return self._derive_(self.module.expanduser(self))

    def expandvars(self):
        """Return the argument with environment variables expanded.
        Substrings of the form $name or ${name} are replaced by the value of
        environment variable name. Malformed variable names and references to
        non-existing variables are left unchanged.
        On Windows, %name% expansions are supported in addition to $name and ${name}."""
        return self._derive_(self.module.expandvars(self))

    def expand(self):
        return self.expanduser().expandvars()

    def listdir(self, pattern=None):
        """Different to os.listdir.
        Accepts an optional pattern for fnmatch.filter
        """
        names = os.listdir(self)
        if pattern:
            return fnmatch.filter(names, pattern)
        return names

    def rename(self, name, *, dry=False):
        path, _ = self.module.split(self)
        path = self.module.join(path, name)
        if not dry:
            os.rename(self, path)
        return self._derive_(path)

    def _name(self, name, *, dry=False):
        return self.rename(name, dry=dry)

    def _stem(self, stem, *, dry=False):
        _, ext = self.module.splitext(self)
        return self._name(stem + ext, dry=dry)

    def _ext(self, ext, *, dry=False):
        if not ext.startswith('.'):
            ext = f'.{ext}'
        path = f'{self.module.splitext(self)[0]}{ext}'
        if not dry:
            os.rename(self, path)
        return self._derive_(path)

    def read(self, buffering=-1, encoding=None, errors='strict'):
        with open(self, mode=f'r{self._mode}', buffering=buffering, encoding=encoding, errors=errors) as f:
            return P_NEWLINE_U.sub('\n', f.read())

    def write(self, text, encoding=None, errors='strict', newline=None, append=False):
        if newline is None:
            newline = os.linesep

        if isinstance(text, str):
            text = P_NEWLINE_U.sub(newline, text)
            text = text.encode(encoding or sys.getdefaultencoding(), errors)

        mode = 'a' if append else 'w'
        with open(self, f'{mode}b') as f:
            f.write(text)

    append = partial(write, append=True)


class FName(FBase):

    def __call__(self, name, *a, **ka):
        return self._parent._name(name, *a, **ka)  # pylint: disable=protected-access

    def __rdiv__(self, rest):
        return self._derive_(rest, self)

    __rtruediv__ = __rdiv__


class FStem(FBase):

    def __call__(self, stem, *a, **ka):
        return self._parent._stem(stem, *a, **ka)  # pylint: disable=protected-access


class FExt(FBase):

    def __radd__(self, other):
        if (self.startswith('.')):
            return self._derive_(str.__add__('.', other).__add__(self[1:]))
        return super(FExt, self).__radd__(str.__add__('.', other))

    def __call__(self, ext, *a, **ka):
        return self._parent._ext(ext, *a, **ka)  # pylint: disable=protected-access


class F(FPath, FIO):  # pylint: disable=invalid-name

    def __call__(self, *rst):
        return self._derive_(*(self, *rst))

    @classproperty
    def DIR(cls):  # pylint: disable=invalid-name
        return cls(os.getcwd())


# ***************************************************************************

TODO('logger')

if __name__ == '__main__':
    print('Woo')
