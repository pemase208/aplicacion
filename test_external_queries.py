#!/usr/bin/env python3
"""
Script de prueba para las consultas externas
RPC: Registro Público Concursal
BOE: Boletín Oficial del Estado
TEU: Tablón Edictal Único
"""

import sys
import os

# Agregar el directorio actual al path para importar las utilidades
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.external_queries import ExternalQueryManager, consultar_rpc, consultar_boe_tablon

def test_consultas():
    """Prueba las consultas externas con un DNI de ejemplo"""
    
    print("🔍 Probando consultas externas...")
    print("=" * 50)
    
    # DNI de ejemplo (deberías usar uno real para pruebas)
    dni_ejemplo = "12345678A"
    
    print(f"DNI de prueba: {dni_ejemplo}")
    print()
    
    # Crear instancia del gestor
    manager = ExternalQueryManager()
    
    try:
        # 1. Prueba RPC
        print("1️⃣ Consultando Registro Público Concursal (RPC)...")
        datos_rpc, mensaje_rpc = manager.consultar_rpc(dni_ejemplo)
        
        if datos_rpc:
            print(f"✅ RPC: Se encontraron {len(datos_rpc)} resultados")
            for i, resultado in enumerate(datos_rpc, 1):
                print(f"   Resultado {i}: {resultado}")
        else:
            print(f"ℹ️ RPC: {mensaje_rpc}")
        
        print()
        
        # 2. Prueba BOE
        print("2️⃣ Consultando Boletín Oficial del Estado (BOE)...")
        datos_boe, mensaje_boe = manager.consultar_boe(dni_ejemplo)
        
        if datos_boe:
            print(f"✅ BOE: Se encontraron {len(datos_boe)} resultados")
            for i, resultado in enumerate(datos_boe, 1):
                print(f"   Resultado {i}: {resultado}")
        else:
            print(f"ℹ️ BOE: {mensaje_boe}")
        
        print()
        
        # 3. Prueba Tablón Edictal
        print("3️⃣ Consultando Tablón Edictal Único (TEU)...")
        datos_teu, mensaje_teu = manager.consultar_tablon_edictal(dni_ejemplo)
        
        if datos_teu:
            print(f"✅ TEU: Se encontraron {len(datos_teu)} resultados")
            for i, resultado in enumerate(datos_teu, 1):
                print(f"   Resultado {i}: {resultado}")
        else:
            print(f"ℹ️ TEU: {mensaje_teu}")
        
        print()
        
        # 4. Prueba consulta completa
        print("4️⃣ Realizando consulta completa...")
        resultados_completos = manager.consultar_completa(dni_ejemplo)
        
        print("📊 Resumen de consulta completa:")
        for fuente, datos in resultados_completos.items():
            if datos['datos']:
                print(f"   {fuente.upper()}: {len(datos['datos'])} resultados")
            else:
                print(f"   {fuente.upper()}: {datos['mensaje']}")
        
        print()
        
        # 5. Prueba funciones de conveniencia
        print("5️⃣ Probando funciones de conveniencia...")
        datos_rpc_simple, mensaje_rpc_simple = consultar_rpc(dni_ejemplo)
        datos_boe_simple, mensaje_boe_simple = consultar_boe_tablon(dni_ejemplo)
        
        print(f"   RPC simple: {len(datos_rpc_simple)} resultados")
        print(f"   BOE+TEU simple: {len(datos_boe_simple)} resultados")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 50)
    print("✅ Pruebas completadas")

def test_con_dni_real():
    """Prueba con un DNI real (opcional)"""
    print("\n🔍 ¿Quieres probar con un DNI real? (s/n): ", end="")
    respuesta = input().strip().lower()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        print("Introduce el DNI/NIE: ", end="")
        dni_real = input().strip().upper()
        
        if dni_real:
            print(f"\n🔍 Probando con DNI real: {dni_real}")
            print("=" * 50)
            
            manager = ExternalQueryManager()
            
            try:
                # Consulta RPC
                print("Consultando RPC...")
                datos_rpc, mensaje_rpc = manager.consultar_rpc(dni_real)
                if datos_rpc:
                    print(f"✅ RPC: {len(datos_rpc)} resultados")
                else:
                    print(f"ℹ️ RPC: {mensaje_rpc}")
                
                # Consulta BOE
                print("Consultando BOE...")
                datos_boe, mensaje_boe = manager.consultar_boe(dni_real)
                if datos_boe:
                    print(f"✅ BOE: {len(datos_boe)} resultados")
                else:
                    print(f"ℹ️ BOE: {mensaje_boe}")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de consultas externas")
    print("Este script prueba la funcionalidad de consultas a:")
    print("  - Registro Público Concursal (RPC)")
    print("  - Boletín Oficial del Estado (BOE)")
    print("  - Tablón Edictal Único (TEU)")
    print()
    
    test_consultas()
    test_con_dni_real()
    
    print("\n🎉 Todas las pruebas han sido completadas")
    print("💡 Recuerda que las consultas reales pueden tardar varios segundos")
    print("   y dependen de la disponibilidad de los servicios externos.")
