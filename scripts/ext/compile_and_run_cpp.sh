#!/bin/bash

set -e
file="$1"

if ! dpkg -s build-essential >/dev/null 2>&1; then
    sudo apt update
    sudo apt install build-essential -y
fi

if [[ "${file}" == *.cpp ]] || [[ "${file}" == *.cc ]]; then
    compiler="g++"
elif [[ "${file}" == *.c ]]; then
    compiler="gcc"
else
    echo "Invalid source file: ${file}"
    exit 1
fi

out_file="${file%.*}"
if [[ "${OSTYPE}" == "msys" ]] || [[ "${OSTYPE}" == "cygwin" ]]; then
    out_file+=".exe"
fi

# Compile if source file is newer than the executable
${compiler} -O2 -pipe -o "${out_file}" "${file}"
echo "Output file: ${out_file}"

chmod +x "${file}"
"${out_file}"
