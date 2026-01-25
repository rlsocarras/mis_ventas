import os
import subprocess
import sys

def encontrar_python():
    """Busca Python en rutas comunes de Odoo"""
    rutas_posibles = [
        r"D:\Instalaciones\Odoo18\python\python.exe",
        r"C:\Program Files\Odoo 18\python\python.exe",
        r"C:\Odoo 18\python\python.exe",
        r"python.exe",  # Si está en PATH
    ]
    
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            return ruta
    
    # Si no se encuentra, pedir al usuario
    print("❌ No se encontró Python automáticamente.")
    ruta_manual = input("Introduce la ruta completa a python.exe: ")
    if os.path.exists(ruta_manual):
        return ruta_manual
    else:
        print("❌ La ruta no existe.")
        sys.exit(1)

def encontrar_servicio():
    """Busca el servicio de Odoo"""
    servicios = ["Odoo18", "Odoo18-server", "Odoo18.0", "Odoo"]
    
    for servicio in servicios:
        try:
            result = subprocess.run(
                ["sc", "query", servicio],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if "STATE" in result.stdout:
                return servicio
        except:
            continue
    
    print("⚠️  No se pudo detectar el servicio automáticamente.")
    return input("Introduce el nombre del servicio Odoo: ")

def actualizar_modulo():
    """Actualiza el módulo"""
    
    # Configuración
    config = {
        'modulo': 'ventas_viaje',
        'base_datos': 'pruebas',  # Cambia esto
        'ruta_odoo': r'D:\Instalaciones\Odoo18\server',
        'python_exe': encontrar_python(),
        'servicio': encontrar_servicio()
    }
    
    print("\n" + "="*50)
    print("CONFIGURACIÓN DETECTADA:")
    print(f"Python: {config['python_exe']}")
    print(f"Odoo: {config['ruta_odoo']}")
    print(f"Servicio: {config['servicio']}")
    print(f"Módulo: {config['modulo']}")
    print(f"Base de datos: {config['base_datos']}")
    print("="*50 + "\n")
    
    # Verificar que odoo-bin existe
    odoo_bin = os.path.join(config['ruta_odoo'], 'odoo-bin')
    if not os.path.exists(odoo_bin):
        print(f"❌ ERROR: No se encuentra odoo-bin en: {odoo_bin}")
        input("Presiona Enter para salir...")
        return
    
    # Comando para actualizar
    comando = [
        config['python_exe'],
        odoo_bin,
        '-u', config['modulo'],
        '-d', config['base_datos'],
        '--addons-path', config['ruta_odoo'],
        '--stop-after-init'
    ]
    
    print("🔄 Actualizando módulo...")
    print(f"Comando: {' '.join(comando)}")
    print("-"*50)
    
    try:
        # Cambiar al directorio de Odoo
        os.chdir(config['ruta_odoo'])
        
        # Ejecutar
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if resultado.returncode == 0:
            print("✅ Módulo actualizado correctamente!")
            
            # Mostrar últimas líneas del output
            lineas = resultado.stdout.strip().split('\n')
            print("\n--- ÚLTIMAS LÍNEAS DEL LOG ---")
            for linea in lineas[-10:]:
                print(linea)
            
            # Preguntar por reinicio
            reiniciar = input("\n¿Reiniciar servicio Odoo? (s/n): ").lower()
            if reiniciar == 's':
                reiniciar_servicio(config['servicio'])
                
        else:
            print("❌ Error al actualizar el módulo")
            print("\n--- ERROR ---")
            print(resultado.stderr[-500:])
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    input("\nPresiona Enter para salir...")

def reiniciar_servicio(nombre_servicio):
    """Reinicia el servicio de Odoo"""
    try:
        print(f"🔄 Reiniciando servicio {nombre_servicio}...")
        
        # Detener
        subprocess.run(
            ["net", "stop", nombre_servicio],
            check=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print("⏹️  Servicio detenido")
        
        # Esperar
        import time
        time.sleep(3)
        
        # Iniciar
        subprocess.run(
            ["net", "start", nombre_servicio],
            check=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print("▶️  Servicio iniciado")
        print(f"✅ Servicio {nombre_servicio} reiniciado correctamente")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error al manejar el servicio: {e}")
        print("💡 Ejecuta como Administrador si ves errores de permisos")

if __name__ == "__main__":
    actualizar_modulo()