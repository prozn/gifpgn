import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(name='gifpgn',
      version='0.2.0',
      description='Convert a PGN into a GIF with stockfish evaluation chart',
      long_description=README,
      long_description_content_type="text/markdown",
      url='http://github.com/prozn/gifpgn',
      author='Prozn',
      license='GPLv3+',
      packages=['gifpgn'],
      python_requires='>=3.7',
      install_requires=['pillow>=8.2.0','stockfish>=3.17.0','chess>=1.6.1'],
      package_data = {
            'gifpgn': ['assets/*.png','fonts/*.ttf'],
      })