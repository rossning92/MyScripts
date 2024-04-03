# https://github.com/baldurk/renderdoc/blob/v1.x/docs/CONTRIBUTING/Compiling.md#windows

set -e

cd "$HOME/Projects/renderdoc"
# upgrade project from VS2015 VS2019 to VS2022
find . -name '*.vcxproj' -execdir sed -i -e "s@<PlatformTool[Ss]et>v14[0123]</PlatformTool[Ss]et>@<PlatformToolset>v143</PlatformToolset>@g" '{}' ';'

run_script r/win/msbuild.cmd renderdoc.sln
