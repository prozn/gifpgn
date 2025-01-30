import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.rst").read_text()

setup(
    name='gifpgn',
    version='1.1.0',
    description='Chess GIF Generator for Python',
    long_description=README,
    long_description_content_type="text/x-rst",
    keywords="chess pgn uci analysis stockfish gif acpl",
    url='http://github.com/prozn/gifpgn',
    author='Matthew Hambly',
    author_email='gifpgn@quickmind.co.uk',
    license='GPLv3+',
    packages=['gifpgn'],
    python_requires='>=3.10',
    install_requires=['pillow==11.1.0', 'chess==1.11.1'],
    package_data={
        'gifpgn': ['assets/pieces/*/*.png', 'assets/nags/*.png', 'fonts/*.ttf'],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Typing :: Typed",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Games/Entertainment :: Real Time Strategy",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
