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

from ruamel.yaml import YAML


from common_types import Library, LibraryType, LibraryStoreType

class BaseBuilder():
  ## Base class for builders
  #


  def __init__(self, params):
    ## Constructor
    
    ''''''
        

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __load_libraries_file(self):

    yaml = YAML(typ='safe', pure=True)
    yaml.default_flow_style = False
    yaml_file = self.config / "libraries.yaml"
    data = yaml.load(yaml_file)

    self.libraries = {}
    libraries = data.get('libraries', {})
    if libraries:
      for lib in libraries:
        library = Library()
        library.name = lib.get('name')
        library.url = lib.get('url')
        library.lib_type = LibraryType[lib.get('type')]
        library.libname = lib.get('libname')
        rl = lib.get('required_libraries')
        if rl:
          for r in rl:
            library.add_required_library(r['name'], r['version'])
        ol = lib.get('optional_libraries')
        if ol:
          for o in ol:
            library.add_optional_library(o['name'], o['version'], o['notes'])

        self.libraries[library.name] = library

    self.set_library_tbl_values(library)

  # ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
  def __save_libraries_file(self):

    yaml = YAML(typ='safe', pure=True)
    yaml.default_flow_style = False
    yaml_file = self.config / "libraries.yaml"

    data = []
    for library in self.libraries:
      l = {}
      l['name'] = library.name
      l['lib_type'] = library.lib_type
      libname = library.libname
      l['libname'] = libname[1]
      l['url'] = library.url
      l['version'] = library.version
      req_libs = []
      for r in library.required_libraries():
        req_lib = {}
        req_lib['name'] = r.name
        req_lib['version'] = r.version
        req_libs = req_lib
      l['required_libraries'] = req_libs
      opt_libs = []
      for o in library.required_libraries():
        opt_lib = {}
        opt_lib['name'] = o.name
        opt_lib['version'] = o.version
        opt_libs = opt_lib
      l['optional_libraries'] = opt_libs
    data.append(l)
    yaml.dump(self, data, yaml_file)
        