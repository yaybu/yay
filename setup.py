import os

version = '0.0.43'

from setuptools import setup, find_packages
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
    install_requires = [
        "PyYAML",
    ],
    extras_require = dict(
        test = [
            'Django',
            'SQLAlchemy',
            ],
        ),
)
