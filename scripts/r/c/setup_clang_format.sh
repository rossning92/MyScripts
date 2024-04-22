# https://clang.llvm.org/docs/ClangFormat.html
clang-format -style=llvm -dump-config >.clang-format
find . -regex '.*\.\(cpp\|hpp\|cu\|cuh\|c\|h\)' -exec clang-format -style=file -i {} \;
