flake8 . > standards.log
@echo off
for %%F in ("standards.log") do if %%~zF EQU 0 echo Code standards check PASSED.
for %%F in ("standards.log") do if %%~zF NEQ 0 echo Code standards check FAILED. Check standards.log for details.
