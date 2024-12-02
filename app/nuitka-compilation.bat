@echo off
python -m nuitka --standalone --onefile --windows-console-mode=disable --include-data-files=resources/mohseni.ico=resources/mohseni.ico --plugin-enable=pyqt5 --windows-icon-from-ico=resources/mohseni.ico --output-dir=dist --remove-output MaxBridge_Assistant.py
pause
