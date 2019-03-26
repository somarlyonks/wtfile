from setuptools import setup


with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='wtfile',
    version='0.0.0',
    description='An insane alternative to pathlib.Path and path.py.',
    license='MIT',
    author='Sy',
    author_email='somarl@live.com',
    packages=['wtfile'],
    install_requires=[]
)
