@echo off
setlocal
powershell -Command "Start-Process cmd -ArgumentList '/k python 4_yolo_opencv_detector.py' -WorkingDirectory '%~dp0' -Verb RunAs"
