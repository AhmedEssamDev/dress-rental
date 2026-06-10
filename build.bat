@echo off
echo ========================================
echo   بناء ملف EXE لبرنامج تأجير الفساتين
echo ========================================
echo.

REM تأكد من تثبيت PyInstaller
pip install pyinstaller >nul 2>&1

echo جاري البناء...
echo.

pyinstaller ^
    --windowed ^
    --noconsole ^
    --onefile ^
    --name "DressRental" ^
    --add-data "images;images" ^
    --clean ^
    main.py

echo.
if exist dist\DressRental.exe (
    echo ========================================
    echo   تم البناء بنجاح!
    echo   الملف: dist\DressRental.exe
    echo ========================================
    echo.
    echo ملاحظات مهمة:
    echo - انسخ ملف DressRental.exe من مجلد dist
    echo - انسخ مجلد images بجانب الملف
    echo - سيتم انشاء dress_rental.db تلقائيا عند اول تشغيل
) else (
    echo ========================================
    echo   فشل البناء! تحقق من الأخطاء أعلاه
    echo ========================================
)
echo.
pause
