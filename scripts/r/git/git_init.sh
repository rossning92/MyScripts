#!/bin/bash

if [ ! -d ".git" ]; then
    git init

    # .gitattribute
    if [ ! -f ".gitattributes" ]; then
        echo "* text=auto eol=lf" >.gitattributes
    fi
fi
