# https://github.com/iddoeldor/frida-snippets

frida -q -D {{ANDROID_SERIAL}} {{PROC_NAME}} --eval '
var x = {};
Process.enumerateModulesSync().forEach(function(m) {
    if (m.name === "{{MODULE_NAME}}") {
        Module.enumerateExportsSync(m.name).map(e=>{
            console.log(`${m.name}!${e.name}`);
        });
    }
});
' | fzf | clip
