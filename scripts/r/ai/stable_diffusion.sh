{{ include('r/git/git_clone.sh', {'GIT_URL': 'https://github.com/AUTOMATIC1111/stable-diffusion-webui'}) }}

# https://github.com/AUTOMATIC1111/stable-diffusion-webui#automatic-installation-on-windows
cmd.exe /c webui-user.bat