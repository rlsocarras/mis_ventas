@echo off
chcp 65001 >nul
cls

echo =========================================
echo   ACTUALIZADOR VENTAS_VIAJE - ODOO 18
echo =========================================

REM CONFIGURACIÓN - AJUSTA ESTOS VALORES
set MODULO=ventas_viaje
set BASE_DATOS=odoo
set RUTA_ODOO=D:\Instalaciones\Odoo18\server
set RUTA_PYTHON=D:\Instalaciones\Odoo18\python\python.exe
set RUTA_ADDONS=D:\Instalaciones\Odoo18\server\addons

echo.
echo 🔍 Verificando rutas...
if not exist "%RUTA_PYTHON%" (
    echo ❌ ERROR: No se encuentra Python en: %RUTA_PYTHON%
    pause
    exit /b 1
)

if not exist "%RUTA_ODOO%\odoo-bin" (
    echo ❌ ERROR: No se encuentra odoo-bin en: %RUTA_ODOO%
    pause
    exit /b 1
)

echo ✅ Rutas verificadas correctamente
echo.
echo 📦 Módulo: %MODULO%
echo 🗃️  Base de datos: %BASE_DATOS%
echo 📁 Ruta Odoo: %RUTA_ODOO%
echo.
echo 🔄 Actualizando módulo...

cd /d "%RUTA_ODOO%"
"%RUTA_PYTHON%" odoo-bin -u %MODULO% -d %BASE_DATOS% --addons-path="%RUTA_ADDONS%" --stop-after-init

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Módulo actualizado correctamente!
    echo.
    set /p REINICIAR="¿Deseas reiniciar el servicio Odoo? (s/n): "
    if /i "%REINICIAR%"=="s" (
        echo.
        echo 🔄 Reiniciando servicio Odoo...
        net stop Odoo18
        timeout /t 3 /nobreak >nul
        net start Odoo18
        echo ✅ Servicio Odoo18 reiniciado
    )
) else (
    echo.
    echo ❌ Error al actualizar el módulo
    echo Código de error: %ERRORLEVEL%
)

echo.
pause