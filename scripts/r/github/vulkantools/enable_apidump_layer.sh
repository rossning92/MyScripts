{{ include('r/android/enable_vulkan_layer.sh',{
    'PKG_NAME': PKG_NAME,
    'VK_LAYER_': '',
    'VK_LAYER_NAME': 'VK_LAYER_LUNARG_api_dump',
    'VK_LAYER_SO': '~/Projects/VulkanTools/build/layersvt/libVkLayer_api_dump.so'
}) }}