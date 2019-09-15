@echo off

if "%~1"=="" (
	echo ERROR: please pass file as argument.
	exit /b 1
)

cd /d "%~dp1"
pandoc "%~nx1" --pdf-engine=xelatex -o "%~n1.pdf" -V CJKmainfont="Microsoft YaHei" --wrap=preserve -f gfm+hard_line_breaks -V geometry=margin=1in
start "" "%~n1.pdf"