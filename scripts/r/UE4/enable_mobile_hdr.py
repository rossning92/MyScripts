from _shutil import *
import stat

ENABLE_VULKAN = False


def add_value(ini_file, section, kvps):
    print('== ' + ini_file + ' ==')
    if os.path.exists(ini_file):
        with open(ini_file) as f:
            lines = f.readlines()
    else:
        lines = []

    lines = [line.rstrip() for line in lines]

    # Remove existing value
    for kvp in kvps:
        k, v = kvp.split('=')
        indices = [i for i in range(len(lines)) if lines[i].startswith(k + '=')]
        lines = [lines[i] for i in range(len(lines)) if i not in indices]

    # Find section
    try:
        i = lines.index(section)
        i += 1

    except ValueError:
        lines.append('')
        lines.append(section)
        i = len(lines)

    # Add value
    lines[i:i] = kvps
    print(section)
    print('\n'.join(kvps))

    # Save to file
    call2('attrib -r "%s"' % ini_file)
    os.makedirs(os.path.dirname(ini_file), exist_ok=True)
    with open(ini_file, 'w') as f:
        f.write('\n'.join(lines))

    print()


chdir(r'{{UE4_PROJECT}}')

add_value('Config/DefaultEngine.ini', '[/Script/AndroidRuntimeSettings.AndroidRuntimeSettings]', [
    '+PackageForOculusMobile=Quest',
    'bSupportsVulkan=True' if ENABLE_VULKAN else '',
    # 'bPackageDataInsideApk=True',
    'bPackageForGearVR=True',  # Mobile
])

add_value('Config/DefaultEngine.ini', '[/Script/Engine.RendererSettings]', [
    'r.MobileHDR=False',
    'vr.MobileMultiView=True',
    'vr.MobileMultiView.Direct=True',
])

add_value('Saved/Config/Windows/Game.ini', '[/Script/UnrealEd.ProjectPackagingSettings]', [
    'BuildConfiguration=PPBC_Shipping',
])

# call2('cls')
# print('\n'.join(lines))
# sys.exit(0)
