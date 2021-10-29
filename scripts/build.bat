:: build.py --build-source-tar --build-zip --build-portable-zip --build-installer
cd ..
pyinstaller src\berean.pyw -i src\images\berean.ico
pause
