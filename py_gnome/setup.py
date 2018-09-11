#!/usr/bin/env python
"""
The master setup.py file for py_gnome

you should be able to run :
    python setup.py develop

to build and install the whole thing in development mode
(it will only work right with distribute, not setuptools)
All the shared C++ code is compiled with  basic_types.pyx

It needs to be imported before any other extensions
(which happens in the gnome.__init__.py file)
"""

import os
import sys
import sysconfig
import glob
import shutil

# to support "develop" mode:
from setuptools import setup, find_packages
from distutils.command.clean import clean

from distutils.extension import Extension
from Cython.Distutils import build_ext

from git import Repo

import numpy as np

# could run setup from anywhere
SETUP_PATH = os.path.dirname(os.path.abspath(__file__))

# cd to SETUP_PATH, run develop or install, then cd back
CWD = os.getcwd()
os.chdir(SETUP_PATH)

repo = Repo('../.')

try:
    branch_name = repo.active_branch.name
except TypeError:
    branch_name = 'no-branch'

last_update = repo.iter_commits().next().committed_datetime.isoformat(),


def target_dir(name):
    '''Returns the name of a distutils build directory'''
    return ('{dirname}.{platform}-{version[0]}.{version[1]}'
            .format(dirname=name,
                    platform=sysconfig.get_platform(),
                    version=sys.version_info))


def target_path(name='temp'):
    '''returns the full build path'''
    return os.path.join('build', target_dir(name))


class cleanall(clean):
    description = ("cleans files generated by 'develop' mode and files "
                   "autogenerated by cython")

    def run(self):
        # call base class clean
        clean.run(self)

        self.clean_python_files()
        self.clean_cython_files()

        rm_dir = ['pyGnome.egg-info', 'build']
        for dir_ in rm_dir:
            print "Deleting auto-generated directory: {0}".format(dir_)
            try:
                shutil.rmtree(dir_)
            except OSError as err:
                if err.errno != 2:  # ignore the not-found error
                    raise

    def clean_python_files(self):
        # clean any byte-compiled python files
        paths = [os.path.join(SETUP_PATH, 'gnome'),
                 os.path.join(SETUP_PATH, 'scripts'),
                 os.path.join(SETUP_PATH, 'tests')]
        exts = ['*.pyc']

        self.clean_files(paths, exts)

    def clean_cython_files(self):
        # clean remaining cython/cpp files
        paths = [os.path.join(SETUP_PATH, 'gnome', 'cy_gnome'),
                 os.path.join(SETUP_PATH, 'gnome', 'utilities', 'geometry')]
        exts = ['*.so', 'cy_*.pyd', 'cy_*.cpp', 'cy_*.c']

        self.clean_files(paths, exts)

    def clean_files(self, paths, exts):
        for path in paths:
            # first, any local files directly under the path
            for ext in exts:
                for f in glob.glob(os.path.join(path, ext)):
                    self.delete_file(f)

            # next, walk any sub-directories
            for root, dirs, _files in os.walk(path, topdown=False):
                for d in dirs:
                    for ext in exts:
                        for f in glob.glob(os.path.join(root, d, ext)):
                            self.delete_file(f)

    def delete_file(self, filepath):
        print "Deleting auto-generated file: {0}".format(filepath)
        try:
            if os.path.isdir(filepath):
                shutil.rmtree(filepath)
            else:
                os.remove(filepath)
        except OSError as err:
            print("Failed to remove {0}. Error: {1}"
                  .format(filepath, err))
            # raise


# setup our environment and architecture
# These should be properties that are used by all Extensions
libfile = ''

# fixme: is this only for the mac?  And aren't there better ways to get the
#        architecture?
if sys.maxsize <= 2 ** 32:
    architecture = 'i386'
else:
    architecture = 'x86_64'

if sys.platform == 'darwin':
    # for the mac -- we need to set the -arch flag
    os.environ['ARCHFLAGS'] = "-arch {0}".format(architecture)

    libfile = 'lib{0}.a'  # OSX static library filename format
elif sys.platform == "win32":
    # We are now pretty much only supporting the Microsoft package:
    #     "Microsoft Visual C++ Compiler for Python 2.7"
    # which is currently available here:
    #     http://www.microsoft.com/en-us/download/details.aspx?id=44266
    #
    # It should have most everything setup, as long as we have the package
    #     setuptools>=6.0
    libfile = '{0}.lib'  # windows static library filename format

# setup our third party libraries environment - for Win32/Mac OSX
# Linux does not use the libraries in third_party_lib. It links against
# netcdf shared objects installed by apt-get
'''
import subprocess


def get_netcdf_libs():
    """
    Find the netcdf4 libaries:

    1) if present rely on nc-config
    2) search for a user env var
    3) try to look directly for conda libs
    4) fall back to the versions distributed with the py_gnome code
    """
    # check for nc-config
    try:
        result = subprocess.check_output(["nc-config", "--libs"]).split()
        lib_dir = result[0]
        libs = result[1:]
        include_dir = subprocess.check_output(["nc-config", "--includedir"])

        print lib_dir
        print libs
        print include_dir
    except OSError:
        raise NotImplementedError("this setup.py needs nc-config "
                                  "to find netcdf libs")

get_netcdf_libs()
'''


if sys.platform is "darwin" or "win32":
    third_party_dir = os.path.join('..', 'third_party_lib')

    # the netCDF environment
    netcdf_base = os.path.join(third_party_dir, 'netcdf-4.3',
                               sys.platform, architecture)
    netcdf_libs = os.path.join(netcdf_base, 'lib')
    netcdf_inc = os.path.join(netcdf_base, 'include')

    if sys.platform == 'win32':
        # also copy the netcdf *.dlls to cy_gnome directory
        # On windows the dlls have the same names for those used by python's
        # netCDF4 module and PyGnome modules. For PyGnome, we had the latest
        # netcdf dlls from UCARR site but this was giving DLL import errors.
        # Netcdf dlls that come with Python's netCDF4 module (C. Gohlke's site)
        # were different from the netcdf4 DLLs we got from UCARR.
        # For now, third_party_lib contains the DLLs installed in site-packages
        # from C. Gohlke's site.
        #
        # Alternatively, we could also look for python netCDF4 package and copy
        # DLLs from site-packages. This way the DLLs used and loaded by PyGnome
        # are the same as the DLL used and expected by netCDF4. PyGnome loads
        # the DLL with cy_basic_types.pyd and it also imports netCDF4 when
        # netcdf_outputters module is imported - this was causing the previous
        # conflict. The DLL loaded in memory should be consistent - that's the
        # best understanding of current issue!
        # STILL WORKING ON A MORE PERMANENT SOLUTION
        win_dlls = os.path.join(netcdf_base, 'bin')
        dlls_path = os.path.join(os.getcwd(), win_dlls)

        for dll in glob.glob(os.path.join(dlls_path, '*.dll')):
            dlls_dst = os.path.join(os.getcwd(), 'gnome/cy_gnome/')

            dll_name = os.path.split(dll)[1]
            if sys.argv[1] == 'cleanall' or sys.argv[1] == 'clean':
                rm_dll = os.path.join(dlls_dst, dll_name)
                if os.path.exists(rm_dll):
                    os.remove(rm_dll)
                    print "deleted: " + rm_dll
            else:
                # Note: weird permissions/file locking thing on Windows --
                #       couldn't delete or overwrite the dll...
                #       so only copy if it's not there already
                if not os.path.isfile(os.path.join(dlls_dst, dll_name)):
                    print "copy: " + dll + " to: " + dlls_dst
                    shutil.copy(dll, dlls_dst)
        netcdf_names = ('netcdf',)
    else:
        netcdf_names = ('hdf5', 'hdf5_hl', 'netcdf', 'netcdf_c++4')

    netcdf_lib_files = [os.path.join(netcdf_libs, libfile.format(l))
                        for l in netcdf_names]


# print netcdf_base
# print netcdf_libs
# print netcdf_inc
# print netcdf_lib_files


# the cython extensions to build -- each should correspond to a *.pyx file
extension_names = ['cy_mover',
                   'cy_helpers',
                   'cy_wind_mover',
                   'cy_current_mover',
                   'cy_cats_mover',
                   'cy_component_mover',
                   'cy_gridcurrent_mover',
                   'cy_gridwind_mover',
                   'cy_ice_mover',
                   'cy_ice_wind_mover',
                   'cy_currentcycle_mover',
                   'cy_ossm_time',
                   'cy_random_mover',
                   'cy_random_vertical_mover',
                   'cy_rise_velocity_mover',
                   'cy_land_check',
                   'cy_grid_map',
                   'cy_shio_time',
                   'cy_grid',
                   'cy_grid_rect',
                   'cy_grid_curv',
                   'cy_weatherers'
                   ]

cpp_files = ['RectGridVeL_c.cpp',
             'MemUtils.cpp',
             'Mover_c.cpp',
             'Replacements.cpp',
             'ClassID_c.cpp',
             'Random_c.cpp',
             'TimeValuesIO.cpp',
             'GEOMETRY.cpp',
             'OSSMTimeValue_c.cpp',
             'TimeValue_c.cpp',
             'RectUtils.cpp',
             'WindMover_c.cpp',
             'CompFunctions.cpp',
             # 'CMYLIST.cpp',
             # 'GEOMETR2.cpp',
             'StringFunctions.cpp',
             'OUTILS.cpp',
             # 'NetCDFMover_c.cpp',
             'CATSMover_c.cpp',
             'CurrentMover_c.cpp',
             'ComponentMover_c.cpp',
             'ShioTimeValue_c.cpp',
             'ShioHeight.cpp',
             'TriGridVel_c.cpp',
             'DagTree.cpp',
             'DagTreeIO.cpp',
             'ShioCurrent1.cpp',
             'ShioCurrent2.cpp',
             'GridCurrentMover_c.cpp',
             'GridWindMover_c.cpp',
             'IceMover_c.cpp',
             'IceWindMover_c.cpp',
             'CurrentCycleMover_c.cpp',
             'TimeGridVel_c.cpp',
             'TimeGridWind_c.cpp',
             'MakeTriangles.cpp',
             'MakeDagTree.cpp',
             'GridMap_c.cpp',
             'GridMapUtils.cpp',
             'RandomVertical_c.cpp',
             'RiseVelocity_c.cpp',
             'Weatherers_c.cpp',
             ]


cpp_code_dir = os.path.join('..', 'lib_gnome')
cpp_files = [os.path.join(cpp_code_dir, f) for f in cpp_files]


# setting the "pyGNOME" define so that conditional compilation
# in the cpp files is done right.
macros = [('pyGNOME', 1), ]

# Build the extension objects

# suppressing certain warnings
compile_args = ["-Wno-unused-function",  # unused function - cython creates a lot
                ]

extensions = []

lib = []
libdirs = []
link_args = []

# List of include directories for cython code.
# append to this list as needed for each platform
include_dirs = [cpp_code_dir,
                np.get_include(),
                netcdf_inc,
                '.']
static_lib_files = netcdf_lib_files

# build cy_basic_types along with lib_gnome so we can use distutils
# for building everything
# and putting it in the correct place for linking.
# cy_basic_types needs to be imported before any other extensions.
# This is being done in the gnome/cy_gnome/__init__.py

# JS NOTE: 'darwin' and 'win32' statically link against netcdf library.
#          On linux, we link against the dynamic netcdf libraries (shared
#          objects) since netcdf, hdf5 can be installed with a package manager.
#          We also don't have the static builds for these.
#          Also, the static_lib_files only need to be linked against
#          lib_gnome in the following Extension.
# CHB NOTE: one of these days, we need to figure out how to build against
#           conda netcdf...

if sys.platform == "darwin":

    print "using these compile arguments:", compile_args
    basic_types_ext = Extension(r'gnome.cy_gnome.cy_basic_types',
                                ['gnome/cy_gnome/cy_basic_types.pyx'] + cpp_files,
                                language='c++',
                                define_macros=macros,
                                extra_compile_args=compile_args,
                                extra_link_args=['-lz', '-lcurl'],
                                extra_objects=static_lib_files,
                                include_dirs=include_dirs,
                                )

    extensions.append(basic_types_ext)
    static_lib_files = []

elif sys.platform == "win32":
    # build our compile arguments
    macros.append(('_EXPORTS', 1))
    macros.append(('_CRT_SECURE_NO_WARNINGS', 1))

    compile_args = ['/EHsc']

    link_args.append('/MANIFEST')

    include_dirs.append(os.path.join(third_party_dir, 'win32_headers'))

    # build our linking arguments
    libdirs.append(netcdf_libs)

    basic_types_ext = Extension(r'gnome.cy_gnome.cy_basic_types',
                                [r'gnome\cy_gnome\cy_basic_types.pyx'] + cpp_files,
                                language='c++',
                                define_macros=macros,
                                extra_compile_args=compile_args,
                                library_dirs=libdirs,
                                extra_link_args=link_args,
                                extra_objects=static_lib_files,
                                include_dirs=include_dirs,
                                )

    extensions.append(basic_types_ext)

    # we will reference this library when building all other extensions
    static_lib_files = [os.path.join(target_path(),
                                     'Release', 'gnome', 'cy_gnome',
                                     'cy_basic_types.lib')]
    libdirs = []

elif sys.platform == "linux2":
    # for some reason I have to create build/temp.linux-i686-2.7
    # else the compile fails saying temp.linux-i686-2.7 is not found
    # required for develop or install mode
    build_temp = target_path()
    if 'clean' not in sys.argv[1:] and not os.path.exists(build_temp):
        os.makedirs(build_temp)

    # Not sure calling setup twice is the way to go - but do this for now
    # NOTE: This is also linking against the netcdf library (*.so), not
    # the static netcdf. We didn't build a NETCDF static library.
    setup(name='pyGnome',  # not required since ext defines this
          cmdclass={'build_ext': build_ext,
                    'cleanall': cleanall},
          ext_modules=[Extension('gnome.cy_gnome.libgnome',
                                 cpp_files,
                                 language='c++',
                                 define_macros=macros,
                                 libraries=['netcdf'],
                                 include_dirs=[cpp_code_dir],
                                 )])

    # In install mode, it compiles and builds libgnome inside
    # lib.linux-i686-2.7/gnome/cy_gnome
    # This should be moved to build/temp.linux-i686-2.7 so cython files
    # build and link properly
    if 'install' in sys.argv[1]:
        bdir = glob.glob(os.path.join('build/*/gnome/cy_gnome', 'libgnome.so'))
        if len(bdir) > 1:
            raise Exception("Found more than one libgnome.so library "
                            "during install mode in 'build/*/gnome/cy_gnome'")
        if len(bdir) == 0:
            raise Exception("Did not find libgnome.so library "
                            "during install mode in 'build/*/gnome/cy_gnome'")

        libpath = os.path.dirname(bdir[0])

    else:
        libpath = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               'gnome', 'cy_gnome')

    # Need this for finding lib during linking and at runtime
    # using -rpath to define runtime path. Use $ORIGIN to define libgnome.so
    # relative to cy_*.so
    os.environ['LDFLAGS'] = "-L{0} -Wl,-rpath='$ORIGIN'".format(libpath)

    # End building C++ shared object
    compile_args = ["-Wl,-rpath,'$ORIGIN'"]

    lib = ['gnome']
    basic_types_ext = Extension(r'gnome.cy_gnome.cy_basic_types',
                                ['gnome/cy_gnome/cy_basic_types.pyx'],
                                language='c++',
                                define_macros=macros,
                                extra_compile_args=compile_args,
                                libraries=lib,
                                include_dirs=include_dirs,
                                )

    extensions.append(basic_types_ext)
    static_lib_files = []

#
# All other lib_gnome-based cython extensions.
# These depend on the successful build of cy_basic_types
#
for mod_name in extension_names:
    cy_file = os.path.join("gnome/cy_gnome", mod_name + ".pyx")
    extensions.append(Extension('gnome.cy_gnome.' + mod_name,
                                [cy_file],
                                language="c++",
                                define_macros=macros,
                                extra_compile_args=compile_args,
                                extra_link_args=link_args,
                                libraries=lib,
                                library_dirs=libdirs,
                                extra_objects=static_lib_files,
                                include_dirs=include_dirs,
                                )
                      )

# and platform-independent cython extensions:
# well...not entirely platform-independent.  We need to pass the link_args
poly_cypath = os.path.join('gnome', 'utilities', 'geometry')
sources = [os.path.join(poly_cypath, 'cy_point_in_polygon.pyx'),
           os.path.join(poly_cypath, 'c_point_in_polygon.c')]

include_dirs = [np.get_include(), '../lib_gnome']
if sys.platform == "win32":
    include_dirs.append(os.path.join(third_party_dir, 'win32_headers'))

extensions.append(Extension("gnome.utilities.geometry.cy_point_in_polygon",
                            sources=sources,
                            include_dirs=include_dirs,
                            extra_compile_args=compile_args,
                            extra_link_args=link_args,
                            ))

extensions.append(Extension("gnome.utilities.file_tools.filescanner",
                            sources=[os.path.join('gnome',
                                                  'utilities',
                                                  'file_tools',
                                                  'filescanner.pyx')],
                            extra_compile_args=compile_args,
                            include_dirs=include_dirs,
                            language="c",
                            ))


def get_version():
    """
    return the version number from the __init__
    """
    for line in open("gnome/__init__.py"):
        if line.startswith("__version__"):
            version = line.strip().split('=')[1].strip().strip("'").strip('"')
            return version
    raise ValueError("can't find version string in __init__")


setup(name='pyGnome',
      version=get_version(),
      ext_modules=extensions,
      packages=find_packages(),
      package_dir={'gnome': 'gnome'},
      package_data={'gnome': ['data/yeardata/*',
                              'outputters/sample.b64',
                              'weatherers/platforms.json'
                              ]},
      # you are not going to be able to "pip install" this anyway
      # -- no need for requirements
      requires=[],   # want other packages here?
      cmdclass={'build_ext': build_ext,
                'cleanall': cleanall},

      # scripts,

      # metadata for upload to PyPI
      author="Gnome team at NOAA ORR ERD",
      author_email="orr.gnome@noaa.gov",
      description=("GNOME (General NOAA Operational Modeling Environment) "
                   "is the modeling tool the Office of Response and "
                   "Restoration's (OR&R) Emergency Response Division uses to "
                   "predict the possible route, or trajectory, a pollutant "
                   "might follow in or on a body of water, such as in an "
                   "oil spill.  "
                   "It can also be used as a customizable general particle "
                   "tracking code.\n"
                   "Branch: {}\n"
                   "LastUpdate: {}"
                   .format(branch_name, last_update)),
      license="Public Domain",
      keywords="oilspill modeling particle_tracking",
      url="https://github.com/NOAA-ORR-ERD/PyGnome"
      )

# Change current working directory back to what user originally had
os.chdir(CWD)
