# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "ArcNLET-Py User's Manual"
copyright = '2023, Michael Core, Wei Mao, and Ming Ye'
author = 'Michael Core, Wei Mao, and Ming Ye'
release = 'December 20th, 2023'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    # Additional extensions you might need
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------

# Autosectionlabel settings
autosectionlabel_prefix_document = True

# Intersphinx settings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    # Add other intersphinx mappings if needed
}

# -- HTML theme settings (for sphinx_rtd_theme) ------------------------------

html_theme_options = {
    'navigation_depth': 4,
    'display_version': True,
    'prev_next_buttons_location': 'both',
    # Additional theme options
}

# -- Custom CSS for centering images and captions ---------------------------

def setup(app):
    app.add_css_file('custom.css')  # Assuming the file name is custom.css
