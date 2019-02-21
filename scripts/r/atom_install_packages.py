import os
import sys
import subprocess

packages = [
    'sublime-style-column-selection',

    # Latex
    'language-latex',
    'latex',
    'latex-autocomplete',

    # Markdown
    'markdown-preview-enhanced',
    'markdown-writer',
    'markdown-image-assistant',
    'markdown-toc',

    # Graphviz
    'language-dot',
    'graphviz-preview-plus',
]

for pkg in packages:
    path = os.path.expanduser('~/.atom/packages/%s' % pkg)
    if not os.path.exists(path):
        subprocess.call('apm install %s' % pkg, shell=True)
