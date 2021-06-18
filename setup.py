import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(name='gifpgn',
      version='0.1.2',
      description='Convert a PGN into a GIF with stockfish evaluation chart',
      long_description=README,
      long_description_content_type="text/markdown",
      url='http://github.com/prozn/gifpgn',
      author='Prozn',
      license='GPLv3+',
      packages=['gifpgn'],
      python_requires='>=3.7',
      install_requires=['pillow','stockfish','chess'],
      package_data = {
            'gifpgn': ['assets/*.png','fonts/*.ttf'],
      })