# https://github.com/iddoeldor/frida-snippets

frida -q --device {{ANDROID_SERIAL}} {{PROC_NAME}} --eval '
Process.enumerateModulesSync().forEach((m)=>{
    console.log(m.name)
});
' | fzf | clip
