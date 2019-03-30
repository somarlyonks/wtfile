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


def TODO(*_):
    scan = False
    if os.getenv('CI'):
        pass
    elif scan:
        raise NotImplementedError(*_)


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
        self.assertEqual(F('/tmp') / 'wtfile' / 'tmp.file', '/tmp/wtfile/tmp.file')
        self.assertEqual(type(F('/tmp') / 'wtfile' / 'tmp.file'), F)


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


class TestPath(TestCase):

    def test_cd(self):
        dir_ = F('/tmp/wtfile/folder')
        self.assertEqual(dir_.cd('..'), '/tmp/wtfile')
        self.assertEqual(dir_.cd('...'), '/tmp')

    def test_cd_root(self):
        dir_ = F('/tmp/wtfile')
        self.assertEqual(dir_.cd('...'), '/')
        self.assertEqual(dir_.cd('...').cd('...'), '/')
        dir_ = F('tmp/wtfile')
        self.assertEqual(dir_.cd('...'), '')
        self.assertEqual(dir_.cd('...').cd('...'), '')


class TestIO(IOCase):

    def test_DIR(self):
        self.assertEqual(F.DIR, os.getcwd())

    @IOCase.scarecrow()
    def test_file_time(self, file):
        self.assertEqual(file.atime, os.path.getatime(file))
        self.assertEqual(file.ctime, os.path.getctime(file))
        self.assertEqual(file.mtime, os.path.getmtime(file))

    @IOCase.scarecrow()
    def test_abspath(self, file):
        self.assertEqual(file.cwd, os.getcwd())
        self.assertEqual(file.abspath, os.path.abspath(file))

    def test_with_block(self):
        TODO()

    TODO()


# order Z: finish
class TestZZZZZZZZZ(TestCase):

    def test_ends(self):
        print('')
        print('tests finished')


if __name__ == '__main__':
    unittest.main()
