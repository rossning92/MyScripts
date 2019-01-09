import os
import sys
import subprocess

packages = [
    # Latex
    'language-latex',
    'latex',
    'latex-autocomplete',

    # Markdown
    'markdown-preview-enhanced',
    'markdown-writer',
    'markdown-image-assistant',

    'sublime-style-column-selection',

    'language-dot',
    'graphviz-preview-plus',
]

for pkg in packages:
    path = os.path.expanduser('~/.atom/packages/%s' % pkg)
    if not os.path.exists(path):
        subprocess.call('apm install %s' % pkg, shell=True)
