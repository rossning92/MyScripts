from _shutil import *
from _cmake import *


def f2():
    if not exists('Vulkan'):
        call2('git clone --recursive https://github.com/SaschaWillems/Vulkan.git')

    chdir('Vulkan')

    if not exists('vulkan_asset_pack.zip'):
        call2('python download_assets.py')

    setup_cmake()
    call2('cmake -G "Visual Studio 15 2017 Win64"')
    call2('start vulkanExamples.sln')


setup_cmake()
mkdir('C:\\Projects')
chdir('C:\\Projects')

# shutil.rmtree('VulkanSamples')

if not exists('VulkanSamples'):
    call2('git clone https://github.com/LunarG/VulkanSamples.git')

chdir('VulkanSamples')
mkdir('build')
chdir('build')

# Reference: https://github.com/LunarG/VulkanSamples/blob/master/BUILD.md
if not exists('glslang'):
    # download and build dependencies
    call2('python ../scripts/update_deps.py --arch x64')


print2('# Create the Visual Studio Project Files')
call2('cmake -C helper.cmake -A x64 ..')

subprocess.call('explorer .')
