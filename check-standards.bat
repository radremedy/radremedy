flake8 . > standards.log
@echo off
for %%F in ("standards.log") do (
	if %%~zF EQU 0 (
		echo Python standards check PASSED.
	) else (
		echo Python standards check FAILED. Check standards.log for details.
		exit /B 1
	)
)
