# https://clang.llvm.org/extra/clang-tidy/
clang-tidy --fix-errors --checks='bugprone-*,cert-*,clang-analyzer-*,concurrency-*,cppcoreguidelines-*,hicpp-*,-hicpp-uppercase-literal-suffix,modernize-*,performance-*,readability-*,-readability-uppercase-literal-suffix,-modernize-use-trailing-return-type' {{C_FILE}} -- -std=c++17
