
#!/usr/bin/env python3

import sys

from setuptools import find_packages, setup

setup(
    name="bibchecker",
    version="0.1.0",
    description="Checks Stuttgart stadtbibliothek",
    author="makefu",
    author_email="github@syntax-fehler.de",
    url="https://github.com/makefu/bibchecker",
    license="MIT",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "bibchecker = bibchecker:main",
        ]
    },
    extras_require={"dev": ["mypy"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
    ],
)
