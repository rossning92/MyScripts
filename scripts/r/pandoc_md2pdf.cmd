@echo off

if "%1"=="" (
	echo Please pass file as parameter.
	pause
)

cd /d "%~dp1"
pandoc "%~nx1" --pdf-engine=xelatex -o "%~n1.pdf" -V CJKmainfont="Microsoft YaHei"