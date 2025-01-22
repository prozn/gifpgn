import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(name='gifpgn',
      version='0.3.0',
      description='Convert a PGN into a GIF with stockfish evaluation chart',
      long_description=README,
      long_description_content_type="text/markdown",
      url='http://github.com/prozn/gifpgn',
      author='Prozn',
      license='GPLv3+',
      packages=['gifpgn'],
      python_requires='>=3.10',
      install_requires=['pillow>=11.1.0','chess>=1.11.1'],
      package_data = {
            'gifpgn': ['assets/*.png','fonts/*.ttf'],
      })