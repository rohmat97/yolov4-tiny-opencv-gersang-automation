@echo off
setlocal
powershell -Command "Start-Process cmd -ArgumentList '/k python \"%~dp0auto_login.py\"' -WorkingDirectory '%~dp0' -Verb RunAs"
