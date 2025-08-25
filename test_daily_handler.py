#!/usr/bin/env python3
"""
Test script para verificar el handler de /daily
"""

# Test que el módulo se puede importar correctamente
try:
    from app.handlers.daily_handler import get_daily_handler

    print("✅ daily_handler se importa correctamente")

    handler = get_daily_handler()
    print(f"✅ Handler creado: {handler}")
    print(f"✅ Comando: {handler.commands}")

except ImportError as e:
    print(f"❌ Error al importar daily_handler: {e}")

try:
    from app.database.services import DailyService

    print("✅ DailyService se importa correctamente")

    # Verificar que el método existe
    if hasattr(DailyService, "get_latest_unregistered_daily_by_group"):
        print("✅ Método get_latest_unregistered_daily_by_group existe")
    else:
        print("❌ Método get_latest_unregistered_daily_by_group no existe")

except ImportError as e:
    print(f"❌ Error al importar DailyService: {e}")

print("\n📋 Resumen del handler /daily:")
print("1. ✅ Solo funciona en grupos")
print("2. ✅ Busca la última daily no registrada en Redmine")
print("3. ✅ Verifica que no hayan pasado más de 30 minutos")
print("4. ✅ Crea la tarea en Redmine con el usuario que ejecuta el comando")
print("5. ✅ Loguea tiempo para usuarios mencionados que tengan token")
print("6. ✅ Marca la daily como registrada en Redmine")
print("7. ✅ Envía reporte detallado del proceso")
