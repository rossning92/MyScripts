echo 'Map remote 5037 to local... (Ctrl-C to close)'
plink -R 5037:localhost:5037 {{SSH_USER}}@{{SSH_HOST}} -pw {{SSH_PWD}}
