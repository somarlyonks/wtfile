import datetime
from functools import wraps
import os
import re
import subprocess
import sys
import unittest
from unittest import TestCase

from wtfile import F
from wtfile import FExt, FStem, FName
from wtfile import TODO


# order 0: makesure tests runable
class Test0Test(TestCase):

    def test_py_version(self):
        self.assertGreaterEqual(sys.version_info, (3, 6, 0))
        print('tests runable')


# order 1: make sure basic logic proper
class Test1Create(TestCase):

    def test_f_init(self):
        try:
            F('/tmp', 'wtfile')
        except Exception:
            self.assertEqual(0, 1)

    def test_f_basic_io(self):
        tmp = F('/tmp')
        tmp = tmp.clear('wtfile')
        self.assertEqual(tmp, '/tmp/wtfile')
        self.assertEqual(tmp.isdir(), True)
        # try again to make sure it's able to remove and recreate
        tmp = F('/tmp', 'wtfile').clear()
        self.assertEqual(tmp, '/tmp/wtfile')
        self.assertEqual(tmp.isdir(), True)


class IOCase(TestCase):

    def setUp(self):
        self.dir = F('/tmp').clear('wtfile')

    def tearDown(self):
        self.dir.rm()

    @staticmethod
    def expect_exception(exception):
        def decorator(fn):
            @wraps(fn)
            def decorated(self, *args, **kwargs):
                self.assertRaises(exception, fn, self, *args, **kwargs)
            return decorated
        return decorator

    @staticmethod
    def scarecrow(name='tmp.file', *, clear=True, cleanup=True):
        if type(name) != str:
            raise TypeError

        def decorator(fn):
            @wraps(fn)
            def decorated(self, *args, **kwargs):
                tmp = F('/tmp/wtfile')
                if clear:
                    tmp.clear()
                f = tmp('tmp.file').touch()

                def _cleanup():
                    if cleanup:
                        tmp.clear()
                    else:
                        f.rm()
                try:
                    fn(self, f, *args, **kwargs)
                except Exception as e:
                    _cleanup()
                    raise e
                else:
                    _cleanup()
            return decorated
        return decorator


# ################################ prepare ################################ #
#                                                                           #
# ################################# tests ################################# #


class TestPerformance(TestCase):

    def test_import_time(self):
        """Run tests in a subprocess to isolate from test suite overhead."""
        cmd = [
            sys.executable,
            '-m', 'timeit',
            '-n', '1',
            '-r', '1',
            'import wtfile',
        ]
        res = subprocess.check_output(cmd, universal_newlines=True)
        dur = re.search(r'(\d+) msec per loop', res).group(1)
        limit = datetime.timedelta(milliseconds=100)
        duration = datetime.timedelta(milliseconds=int(dur))
        self.assertLess(duration, limit)


class TestSelf(TestCase):

    def test_init_empty(self):
        self.assertEqual(F(), '')

    def test_call(self):
        dir_ = F('/tmp/wtfile')
        self.assertEqual(dir_('folder')('tmp.file'), '/tmp/wtfile/folder/tmp.file')
        self.assertEqual(dir_('folder', 'tmp.file'), '/tmp/wtfile/folder/tmp.file')

    def test_add(self):
        self.assertEqual(F('') + 'x', 'x')
        self.assertEqual(F('/tmp') + '/wtfile', '/tmp/wtfile')
        self.assertEqual(type(F('/tmp') + '/wtfile'), F)

    def test_radd(self):
        self.assertEqual('x' + F(''), 'x')
        self.assertEqual('/tmp' + F('/wtfile'), '/tmp/wtfile')
        self.assertEqual(type('/tmp' + F('/wtfile')), F)

    def test_div(self):
        self.assertEqual('/tmp' / F('wtfile') / 'tmp.file', '/tmp/wtfile/tmp.file')
        self.assertEqual(type('/tmp' / F('wtfile') / 'tmp.file'), F)

    def test_to_str(self):
        f = F('/tmp/wtfile')
        self.assertEqual(f.to_str(), '/tmp/wtfile')
        self.assertEqual(type(f.to_str()), str)


class TestComponents(IOCase):

    @IOCase.scarecrow()
    def test_ext(self, file):
        self.assertEqual(file.ext, '.file')
        self.assertEqual(type(file.ext), FExt)

    @IOCase.scarecrow()
    def test_stem(self, file):
        self.assertEqual(file.stem, 'tmp')
        self.assertEqual(type(file.stem), FStem)

    @IOCase.scarecrow()
    def test_name(self, file):
        self.assertEqual(file.name, 'tmp.file')
        self.assertEqual(type(file.name), FName)

    @IOCase.scarecrow()
    def test_add(self, file):
        self.assertEqual(file.ext + 'x', '.filex')
        self.assertEqual(file.stem + 'x', 'tmpx')
        self.assertEqual(file.name + 'x', 'tmp.filex')
        self.assertEqual(type(file.ext + 'x'), FExt)
        self.assertEqual(type(file.stem + 'x'), FStem)
        self.assertEqual(type(file.name + 'x'), FName)

    @IOCase.scarecrow()
    def test_radd(self, file):
        self.assertEqual('x' + file.ext, '.xfile')
        self.assertEqual('x' + F('file').ext, '.x')
        self.assertEqual('x' + file.stem, 'xtmp')
        self.assertEqual('x' + file.name, 'xtmp.file')
        self.assertEqual(type('x' + file.ext), FExt)
        self.assertEqual(type('x' + file.stem), FStem)
        self.assertEqual(type('x' + file.name), FName)

    @IOCase.scarecrow()
    def test_call(self, file):
        file = file.ext('xfile')
        self.assertEqual(file.ext, '.xfile')
        self.assertListEqual(os.listdir(self.dir), ['tmp.xfile'])
        file = file.ext('.xfile')
        self.assertEqual(file.ext, '.xfile')
        self.assertListEqual(os.listdir(self.dir), ['tmp.xfile'])
        file = file.stem('tmpx')
        self.assertEqual(file.stem, 'tmpx')
        self.assertListEqual(os.listdir(self.dir), ['tmpx.xfile'])
        file = file.name('tmp.file')
        self.assertEqual(file.name, 'tmp.file')
        self.assertListEqual(os.listdir(self.dir), ['tmp.file'])

    @IOCase.expect_exception(TypeError)
    @IOCase.scarecrow()
    def test_div(self, file):
        file.ext / 'x'

    @IOCase.scarecrow()
    def test_dry(self, file):
        file = file.ext('xfile', dry=True)
        self.assertEqual(file.ext, '.xfile')
        self.assertEqual(type(file.ext), FExt)
        self.assertListEqual(os.listdir(self.dir), ['tmp.file'])
        file = file.stem('t', dry=True)
        self.assertEqual(file.stem, 't')
        self.assertEqual(type(file.stem), FStem)
        self.assertListEqual(os.listdir(self.dir), ['tmp.file'])


class TestPath(TestCase):

    def test_cd(self):
        dir_ = F('/tmp/wtfile/folder')
        self.assertEqual(dir_.cd('..'), '/tmp/wtfile')
        self.assertEqual(dir_.cd('...'), '/tmp')
        self.assertEqual(dir_.cd('subfolder'), '/tmp/wtfile/folder/subfolder')
        self.assertEqual(dir_.cd('./subfolder'), '/tmp/wtfile/folder/subfolder')
        self.assertEqual(dir_.cd('../folder2'), '/tmp/wtfile/folder2')

    def test_cd_root(self):
        dir_ = F('/tmp/wtfile')
        self.assertEqual(dir_.cd('...'), '/')
        self.assertEqual(dir_.cd('...').cd('...'), '/')
        dir_ = F('tmp/wtfile')
        self.assertEqual(dir_.cd('...'), '')
        self.assertEqual(dir_.cd('...').cd('...'), '')

    def test_norm(self):
        f = F('/tmp/./wtfile')
        self.assertEqual(f.norm(), '/tmp/wtfile')
        self.assertEqual(f.normal(), '/tmp/wtfile')

    def test_match(self):
        f = F('/tmp/wtfile/stem.ext')
        self.assertEqual(f.match('*.ext'), True)
        self.assertEqual(f.match('*.xt'), False)
        self.assertEqual(F('x.xt').match('*.ext'), False)

    def test_matchcase(self):
        f = F('/tmp/wtfile/stem.eXt')
        self.assertEqual(f.matchcase('*.eXt'), True)
        self.assertEqual(f.matchcase('*.ext'), False)
        self.assertEqual(f.matchcase('*.xt'), False)
        self.assertEqual(F('x.ext').match('*.eXt'), False)

    def test_root(self):
        self.assertEqual(F('/tmp/wtfile').root, '/')
        self.assertEqual(F('~/tmp/wtfile').root, '~')
        self.assertEqual(F('./tmp/wtfile').root, '.')
        self.assertEqual(F('tmp').root, 'tmp')
        self.assertEqual(F('tmp/wtfile').root, 'tmp')


class TestIO(IOCase):

    def test_DIR(self):
        self.assertEqual(F.DIR, os.getcwd())

    @IOCase.expect_exception(AttributeError)
    def test_set_DIR(self):
        F().DIR = '/tmp'

    @IOCase.scarecrow()
    def test_file_time(self, file):
        self.assertEqual(file.atime, os.path.getatime(file))
        self.assertEqual(file.ctime, os.path.getctime(file))
        self.assertEqual(file.mtime, os.path.getmtime(file))

    @IOCase.scarecrow()
    def test_abspath(self, file):
        self.assertEqual(file.cwd, os.getcwd())
        self.assertEqual(file.abspath, os.path.abspath(file))

    @IOCase.scarecrow()
    def test_rm(self, file):
        file.rm()  # folder rm tested in scarecrow
        self.assertListEqual(os.listdir(self.dir), [])

    @IOCase.expect_exception(TypeError)
    def test_rm_exception(self):
        self.dir('tmp.file').rm()

    @IOCase.scarecrow()
    def test_clear(self, file):
        self.dir.clear('tmp.file')  # folder rm tested in scarecrow
        TODO()  # todo: check the content of the file when read/write finished
        self.assertListEqual(os.listdir(self.dir), ['tmp.file'])

    def test_with_block(self):
        pwd = os.getcwd()
        self.assertNotEqual(F.DIR, self.dir)
        with self.dir as DIR:
            self.assertEqual(DIR, '/tmp/wtfile')
            self.assertEqual(F.DIR, '/tmp/wtfile')
        self.assertEqual(F.DIR, pwd)

    def test_with_nested_block(self):
        pwd = os.getcwd()
        self.assertNotEqual(F.DIR, self.dir)
        with self.dir as DIR:
            self.assertEqual(DIR, '/tmp/wtfile')
            self.dir.mkdir('folder')
            with self.dir / 'folder' as DIR2:
                self.assertEqual(DIR2, '/tmp/wtfile/folder')
        self.assertEqual(F.DIR, pwd)

    @IOCase.expect_exception(TypeError)
    def test_with_nested_block_exception(self):
        pwd = os.getcwd()
        self.assertNotEqual(F.DIR, self.dir)
        with self.dir as DIR:
            self.assertEqual(DIR, '/tmp/wtfile')
            self.dir.mkdir('folder')
            with self.dir as DIR2:
                self.assertEqual(DIR2, '/tmp/wtfile/folder')
        self.assertEqual(F.DIR, pwd)

    def test_expanduser(self):
        user = os.getenv('USER')
        self.assertEqual(F('~/tmp').expanduser(), f'/home/{user}/tmp')
        self.assertEqual(F('/~/tmp').expanduser(), f'/~/tmp')

    def test_expandvars(self):
        user = os.getenv('USER')
        self.assertEqual(F('$USER/tmp').expandvars(), f'{user}/tmp')
        self.assertEqual(F('/$USER/tmp').expandvars(), f'/{user}/tmp')

    def test_expand(self):
        user = os.getenv('USER')
        self.assertEqual(F('~/tmp/$USER/x').expand(), f'/home/{user}/tmp/{user}/x')

    @IOCase.scarecrow()
    def test_listdir(self, file):
        self.assertListEqual(self.dir.listdir(), [file.name])

    @IOCase.scarecrow()
    def test_listdir_match(self, file):
        self.assertListEqual(self.dir.listdir('*.file'), [file.name])
        self.assertListEqual(self.dir.listdir('*.py'), [])

    @IOCase.scarecrow()
    def test_listdir_parent_children(self, file):
        self.assertEqual(file.parent, '/tmp/wtfile')
        self.assertListEqual(file.parent.children, [file.name])

    @IOCase.scarecrow()
    def test_iter(self, file):
        for f in self.dir:
            self.assertEqual(f.name, file.name)

    @IOCase.scarecrow()
    def test_iter_file(self, file):
        file.write('\n'.join(map(str, range(10))))
        for i, line in enumerate(file):
            self.assertEqual(str(i), line)

    @IOCase.scarecrow()
    def test_read(self, file):
        self.assertEqual(file.read(), '')

    @IOCase.scarecrow()
    def test_write(self, file):
        file.write('\n'.join(map(str, range(10))), newline='\n')
        self.assertEqual(file.read(), '\n'.join(map(str, range(10))))

    @IOCase.scarecrow()
    def test_size(self, file):
        self.assertEqual(self.dir.size, 0)
        self.assertEqual(self.dir.getSize(inode=True), 1 << 12)
        self.assertEqual(file.size, 0)
        file.write('123')
        size = self.dir.size
        self.assertNotEqual(file.size, 0)
        self.assertNotEqual(self.dir.size, 0)
        dir2 = self.dir.mkdir('tmp2')
        dir2.mkfile('tmp2.file').write('234')
        self.assertNotEqual(dir2.size, 0)
        self.assertEqual(self.dir.size, size)
        self.assertNotEqual(self.dir.getSize(deep=True), size)

    @IOCase.scarecrow()
    def test_glob(self, file):
        with self.dir as DIR:
            self.assertListEqual(DIR.glob('*.file'), [file.name])

    @IOCase.scarecrow()
    def test_glob_relative(self, file):
        self.assertListEqual(self.dir.glob('*.file', relative=True), [self.dir / file.name])

    @IOCase.scarecrow()
    def test_glob_recursive(self, file):
        self.dir.mkdir('tmp2').mkdir('tmp3').mkfile('tmp.xfile')
        with self.dir as DIR:
            self.assertListEqual(
                DIR.glob('**/*.xfile', recursive=True),
                ['tmp2/tmp3' / file.ext('xfile', dry=True).name]
            )

    @IOCase.scarecrow()
    def test_iglob(self, file):
        with self.dir as DIR:
            self.assertListEqual(list(DIR.iglob('*.file')), [file.name])

    @IOCase.scarecrow()
    def test_iglob_relative(self, file):
        self.assertListEqual(list(self.dir.iglob('*.file', relative=True)), [self.dir / file.name])

    @IOCase.scarecrow()
    def test_islink(self, file):
        link = self.dir('tmp2.file')
        link.linkto(file)
        self.assertEqual(file.islink(), False)
        self.assertEqual(link.islink(), True)

    def test_isabs(self):
        self.assertEqual(F('/tmp/wtfile').isabs(), True)
        self.assertEqual(F('tmp/wtfile').isabs(), False)

    @IOCase.scarecrow()
    def test_ismount(self, file):
        self.assertEqual(file.ismount(), False)
        self.assertEqual(F('/').ismount(), True)

    @IOCase.scarecrow()
    def test_link(self, file):
        link = file.linkfrom(self.dir / 'tmp2.file')
        file.write('123')
        self.assertEqual(link.islink(), True)
        self.assertEqual(link.read(), '123')


# order Z: finish
class TestZZZZZZZZZ(TestCase):

    def test_ends(self):
        print('')
        print('tests finished')


if __name__ == '__main__':
    unittest.main()
