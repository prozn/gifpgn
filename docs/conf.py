# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'gifpgn'
copyright = '2025, Matthew Hambly'
author = 'Matthew Hambly'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

#templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_use_index = False
#html_theme = 'alabaster'
#html_static_path = ['_static']

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration

todo_include_todos = True
autoapi_add_toctree_entry = False

import os
import sys
sys.path.insert(0,os.path.abspath('../'))

def skip(app, what, name, obj,would_skip, options):
    if name in ( '__init__',):
        return True
    
    exclusions = (
        'setup',
        'test',
        'test_chess'
    )
    if name in exclusions:
        return True

    return would_skip

def setup(app):
    app.connect('autodoc-skip-member', skip)
