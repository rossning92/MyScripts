# https://www.kernel.org/doc/html/latest/process/coding-style.html#linux-kernel-coding-style
set -e
cd {{KERNEL_SOURCE_DIR}}
git format-patch HEAD^ --stdout >patchfile.patch
./scripts/checkpatch.pl patchfile.patch --no-signoff --fix-inplace
ls -lah patchfile.patch*
