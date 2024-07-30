field='VIRT,RES,SHR,%MEM'
echo "$field"
adb shell "top -q -d 1 -b -o $field -p \$(pidof \"{{_PROC_NAME}}\") | grep -v \"^$\""
