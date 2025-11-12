#!/bin/bash

set -e
file="$1"

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
${compiler} -O2 -pipe -lm -lcrypto -o "${out_file}" "${file}"
echo "Output file: ${out_file}"

chmod +x "${file}"

# Check if there's a -- in the arguments
if [[ "$@" == *"--"* ]]; then
    # Extract everything after --
    args=$(echo "$@" | sed 's/.*--//')
    "./${out_file}" $args
else
    "./${out_file}"
fi
