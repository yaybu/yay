import os
from setuptools import setup, find_packages
from distutils.command.sdist import sdist
from distutils.command.build_py import build_py

version = '3.0.1'


class generate_ply_tabs:

    def build_ply_tabs(self):
        import ply
        import sys

        sys.path.insert(0, os.path.dirname(os.path.abspath(".")))

        for path in ("yay/lextab.py", "yay/lextab.pyc", "yay/parsetab.py", "yay/parsetab.pyc"):
            if os.path.exists(path):
                print "Deleting %s" % path
                os.remove(path)

        print "Creating lexer"
        from yay.lexer import Lexer
        Lexer()

        print "Creating parser"
        from yay.parser import Parser
        Parser()

        if not os.path.exists("yay/parsetab.py"):
            print "FAILED: parsetab not created"
            os.remove("yay/parsetab.py")
            sys.exit(1)

        if not os.path.exists("yay/lextab.py"):
            print "FAILED: lextab not created"
            os.remove("yay/lextab.py")
            sys.exit(1)


class sdist_with_ply(generate_ply_tabs, sdist):
    def run(self, *args, **kwargs):
        self.build_ply_tabs()
        sdist.run(self, *args, **kwargs)


class build_py_with_ply(generate_ply_tabs, build_py):
    def run(self, *args, **kwargs):
        self.build_ply_tabs()
        build_py.run(self, *args, **kwargs)


setup(
    name='yay',
    description='An extensible config file format',
    long_description = open("README.rst").read() + "\n" + \
                        open("CHANGES").read(),
    version=version,
    url='http://pypi.python.org/pypi/yay',
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: System :: Systems Administration",
    ],
    author='John Carr',
    author_email='john.carr@isotoma.com',
    license="Apache Software License",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    setup_requires = ['ply'],
    install_requires = [
        "ply",
        # "gpglib",
    ],
    extras_require = dict(
        test = [
            "mock",
            "unittest2",
            ],
        ),
    entry_points = {
        'console_scripts': [
            'yay = yay.transform:main',
            ],
        },
    cmdclass = {
        'sdist': sdist_with_ply,
        'build_py': build_py_with_ply,
        },
    )

