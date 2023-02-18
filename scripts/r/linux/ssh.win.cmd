@echo off
ssh -t %SSH_USER%@%SSH_HOST% -o "StrictHostKeyChecking no"
