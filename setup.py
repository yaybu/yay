import os

version = '0.0.0'

from setuptools import setup, find_packages
setup(name='yay',
      version=version,
      packages=['yay'],
      zip_safe=False,
      include_package_data=True,
      install_requires = [
          "ordereddict",
          "PyYAML",
      ],
)
