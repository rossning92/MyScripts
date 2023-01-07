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

pronsole -e connect -e block_until_online
