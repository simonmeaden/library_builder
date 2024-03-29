"""

Copyright 2019 Simon Meaden

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

@author: Simon Meaden

"""

from setuptools import setup

setup(name='Library Builder',
      version='0.1.0dev',
      description='Linux library builder',
      author='Simon Meaden',
      author_email='simon.meaden@virginmedia.com',
      license='license.txt',
      url='https://github.com/simonmeaden/library_builder/blob/master/src/file_reader.py',
      long_description=open('README.md').read(),
      packages=[],
      py_modules=['library_builder',
                  'main_window',
                  'file_reader',
                  'common_types'],
      install_requires=[
          'pygit2',
          'PySide2',
          'ruamel.yaml',
          'urlgrabber',
          'pycurl',
          'gitdb',
          'urllib'
          'python-hglib'
      ],
      )
