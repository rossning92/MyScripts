cat >~/.pronsolerc <<EOF
macro preheat
    M140 S45
    M104 S185

macro stop
    M106 S0 ; turn off cooling fan
    M104 S0 ; turn off extruder
    M140 S0 ; turn off bed
    M84 ; disable motors
EOF

if ! screen -list | grep -q "3dp"; then
    screen -mS 3dp bash -c 'pronsole -e connect -e block_until_online'
else
    screen -x 3dp
fi
