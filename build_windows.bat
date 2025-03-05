@echo off
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing requirements...
pip install -r requirements.txt

echo Building executable...
pyinstaller --name="DBCD Viewer" ^
            --windowed ^
            --icon=DBCD/icons/app_icon.ico ^
            --add-data="README.md;." ^
            --noconsole ^
            --clean ^
            main.py

echo Build complete!
echo Executable can be found in dist/DBCD Viewer/
pause 