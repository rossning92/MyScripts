# https://github.com/baldurk/renderdoc/blob/v1.x/docs/CONTRIBUTING/Compiling.md#windows

set -e
# upgrade to vs2019
find . -name '*.vcxproj' -execdir sed -i -e "s@<PlatformToolset>v14[012]</PlatformToolset>@<PlatformToolset>v142</PlatformToolset>@g" '{}' ';'

cd "{{RENDERDOC_SOURCE}}"
run_script r/win/msbuild.cmd renderdoc.sln
