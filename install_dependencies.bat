@echo off
chcp 65001 >nul
echo ======================================================================
echo                     Dependencies Installation
echo ======================================================================
echo.

echo Installing core packages...
echo.

pip install Flask==2.3.0
pip install Werkzeug==2.3.0
pip install Flask-SQLAlchemy==3.0.5
pip install SQLAlchemy==2.0.19
pip install Flask-Login==0.6.2
pip install Flask-WTF==1.1.1
pip install WTForms==3.0.1
pip install python-magic-bin==0.4.14
pip install Pillow==10.0.0

echo.
echo ======================================================================
echo Installation complete!
echo ======================================================================
echo.

echo Optional: Install testing tools? (y/n)
set /p INSTALL_TEST="Your choice: "

if /i "%INSTALL_TEST%"=="y" (
    echo.
    echo Installing testing tools...
    pip install pytest==7.4.0
    pip install pytest-cov==4.1.0
    echo Testing tools installed!
)

echo.
echo ======================================================================
echo All done! You can now run the application.
echo ======================================================================
pause