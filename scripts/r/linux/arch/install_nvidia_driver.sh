# Install proprietary NVIDIA GPU driver.
# https://wiki.archlinux.org/title/NVIDIA#Xorg_configuration
if lspci -k | grep -q "NVIDIA Corporation"; then
    pac_install nvidia-open nvidia-settings
    sudo nvidia-xconfig --metamodes="nvidia-auto-select +0+0 {ForceCompositionPipeline=On, ForceFullCompositionPipeline=On}" --output-xconfig /etc/X11/xorg.conf.d/20-nvidia.conf
fi
