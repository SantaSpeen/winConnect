# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

from setuptools import setup

_name = 'winConnect'

packages = [_name]
package_dir = {_name: _name}
lib_path = Path(_name).resolve()


# 'setup.py publish' shortcut.
if sys.argv[-1] == 'publish':
    os.system('py -m build')
    os.system('py -m twine upload --repository pypi dist/*')
    sys.exit()

with open(lib_path.parent / 'requirements.txt', 'r', encoding='utf-8') as f:
    requires = f.read().splitlines()

about = {}
with open(lib_path / '__init__.py', 'r', encoding='utf-8') as f:
    exec(f.read(), about)

with open(lib_path.parent / 'README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=packages,
    package_data={'': ['LICENSE']},
    package_dir=package_dir,
    include_package_data=True,
    install_requires=requires,
    license=about['__license__'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: Russian",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: MIT License",
        "Operating System :: Windows",
    ],
    project_urls={
        'Source': 'https://github.com/SantaSpeen/winConnect',
    },
    python_requires=">=3.10",
)