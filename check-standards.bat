flake8 . > standards.log
@echo off
for %%F in ("standards.log") do (
	if %%~zF EQU 0 (
		echo Python standards check PASSED.
	) else (
		echo Python standards check FAILED.
		type standards.log
		exit /B 1
	)
)
