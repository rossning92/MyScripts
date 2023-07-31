#!/bin/bash

if [ ! -f "package.json" ]; then
    yarn config set init-author-name "Ross Ning"
    yarn config set init-author-email rossning92@gmail.com
    yarn init -y
fi
