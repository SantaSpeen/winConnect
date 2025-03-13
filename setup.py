# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

from setuptools import setup

here = Path(__file__).parent.resolve()
_name = 'winConnect'

packages = [_name, ]
package_dir = {_name: _name}
lib_path = here / _name

requires = {
    "install_requires": [
        "pywin32==309",
        "ormsgpack==1.8.0"
    ],
    "extra_packages": {
        "crypto": [
            "pycryptodome==3.21.0"
        ]
    }
}

# 'setup.py publish' shortcut.
if sys.argv[-1] == 'publish':
    os.system('py -m build')
    os.system('py -m twine upload -r pypi dist/*')
    sys.exit()

with open(here / 'README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

about = {}
with open(lib_path / '__meta__.py', 'r', encoding='utf-8') as f:
    exec(f.read(), about)

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
    **requires,
    license=about['__license__'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    project_urls={
        'Source': 'https://github.com/SantaSpeen/winConnect',
    },
    python_requires=">=3.10",
)