#!/usr/bin/env python3
"""
Script para importar entidades bancarias desde archivo XLS
"""

import pandas as pd
from app import app, db
from models import Banco
import os

def importar_bancos_desde_xls(archivo_xls):
    """Importa bancos desde un archivo XLS"""
    try:
        # Leer el archivo XLS
        df = pd.read_excel(archivo_xls)
        
        print(f"Archivo leído correctamente. Filas encontradas: {len(df)}")
        print(f"Columnas detectadas: {list(df.columns)}")
        
        # Mostrar las primeras filas para verificar
        print("\nPrimeras 5 filas del archivo:")
        print(df.head())
        
        # Mapeo de columnas (ajustar según tu archivo)
        # Asumiendo que tienes columnas como: Nombre, Dirección, Número, CP, Localidad, Provincia, CCAA
        mapeo_columnas = {
            'nombre': ['Nombre', 'BANCO', 'ENTIDAD', 'NOMBRE_BANCO', 'BANCO_NOMBRE'],
            'direccion': ['Dirección', 'DIRECCION', 'DIR', 'CALLE', 'DIRECCION_BANCO'],
            'num': ['Número', 'NUM', 'NUMERO', 'Nº', 'NUMERO_BANCO'],
            'cp': ['CP', 'Código Postal', 'CODIGO_POSTAL', 'POSTAL', 'CP_BANCO'],
            'localidad': ['Localidad', 'LOCALIDAD', 'CIUDAD', 'POBLACION', 'LOCALIDAD_BANCO'],
            'provincia': ['Provincia', 'PROVINCIA', 'PROV', 'PROVINCIA_BANCO'],
            'ccaa': ['CCAA', 'Comunidad Autónoma', 'COMUNIDAD', 'AUTONOMA', 'CCAA_BANCO']
        }
        
        # Encontrar las columnas correctas
        columnas_encontradas = {}
        for campo, posibles_nombres in mapeo_columnas.items():
            for nombre in posibles_nombres:
                if nombre in df.columns:
                    columnas_encontradas[campo] = nombre
                    break
        
        print(f"\nColumnas mapeadas: {columnas_encontradas}")
        
        # Verificar que tenemos al menos el nombre
        if 'nombre' not in columnas_encontradas:
            print("ERROR: No se encontró columna de nombre del banco")
            print("Columnas disponibles:", list(df.columns))
            return False
        
        # Importar datos
        bancos_creados = 0
        bancos_existentes = 0
        
        for index, row in df.iterrows():
            nombre = str(row[columnas_encontradas['nombre']]).strip()
            
            # Verificar si el banco ya existe
            banco_existente = Banco.query.filter_by(nombre=nombre).first()
            if banco_existente:
                bancos_existentes += 1
                continue
            
            # Crear nuevo banco
            nuevo_banco = Banco(
                nombre=nombre,
                direccion=str(row.get(columnas_encontradas.get('direccion', ''), '')).strip(),
                num=str(row.get(columnas_encontradas.get('num', ''), '')).strip(),
                cp=str(row.get(columnas_encontradas.get('cp', ''), '')).strip(),
                localidad=str(row.get(columnas_encontradas.get('localidad', ''), '')).strip(),
                provincia=str(row.get(columnas_encontradas.get('provincia', ''), '')).strip(),
                ccaa=str(row.get(columnas_encontradas.get('ccaa', ''), '')).strip()
            )
            
            db.session.add(nuevo_banco)
            bancos_creados += 1
            
            # Mostrar progreso cada 100 bancos
            if bancos_creados % 100 == 0:
                print(f"Procesados {bancos_creados} bancos...")
        
        # Guardar cambios
        db.session.commit()
        
        print(f"\n✅ Importación completada:")
        print(f"   - Bancos creados: {bancos_creados}")
        print(f"   - Bancos existentes (omitidos): {bancos_existentes}")
        print(f"   - Total procesados: {bancos_creados + bancos_existentes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la importación: {str(e)}")
        db.session.rollback()
        return False

def importar_bancos_desde_csv(archivo_csv):
    """Importa bancos desde un archivo CSV"""
    try:
        # Leer el archivo CSV
        df = pd.read_csv(archivo_csv, encoding='utf-8')
        
        print(f"Archivo CSV leído correctamente. Filas encontradas: {len(df)}")
        print(f"Columnas detectadas: {list(df.columns)}")
        
        # Usar la misma lógica que para XLS
        return importar_bancos_desde_xls(archivo_csv)
        
    except Exception as e:
        print(f"❌ Error leyendo archivo CSV: {str(e)}")
        return False

def mostrar_bancos_existentes():
    """Muestra los bancos existentes en la base de datos"""
    bancos = Banco.query.all()
    print(f"\n📊 Bancos existentes en la BD: {len(bancos)}")
    
    if len(bancos) > 0:
        print("\nPrimeros 10 bancos:")
        for i, banco in enumerate(bancos[:10]):
            print(f"  {i+1}. {banco.nombre} - {banco.localidad}, {banco.provincia}")
        
        if len(bancos) > 10:
            print(f"  ... y {len(bancos) - 10} más")

if __name__ == "__main__":
    with app.app_context():
        print("🏦 Importador de Entidades Bancarias")
        print("=" * 50)
        
        # Mostrar bancos existentes
        mostrar_bancos_existentes()
        
        # Buscar archivos en el directorio actual
        archivos_xls = [f for f in os.listdir('.') if f.endswith(('.xls', '.xlsx'))]
        archivos_csv = [f for f in os.listdir('.') if f.endswith('.csv')]
        
        if archivos_xls:
            print(f"\n📁 Archivos XLS/XLSX encontrados: {archivos_xls}")
            for archivo in archivos_xls:
                print(f"\n¿Importar {archivo}? (s/n): ", end="")
                respuesta = input().lower()
                if respuesta == 's':
                    print(f"\n🔄 Importando {archivo}...")
                    if importar_bancos_desde_xls(archivo):
                        print("✅ Importación exitosa")
                    else:
                        print("❌ Error en la importación")
                    break
        
        elif archivos_csv:
            print(f"\n📁 Archivos CSV encontrados: {archivos_csv}")
            for archivo in archivos_csv:
                print(f"\n¿Importar {archivo}? (s/n): ", end="")
                respuesta = input().lower()
                if respuesta == 's':
                    print(f"\n🔄 Importando {archivo}...")
                    if importar_bancos_desde_csv(archivo):
                        print("✅ Importación exitosa")
                    else:
                        print("❌ Error en la importación")
                    break
        
        else:
            print("\n📁 No se encontraron archivos XLS/XLSX o CSV en el directorio actual")
            print("Coloca tu archivo en este directorio y ejecuta el script nuevamente")
        
        # Mostrar resultado final
        print("\n" + "=" * 50)
        mostrar_bancos_existentes()







