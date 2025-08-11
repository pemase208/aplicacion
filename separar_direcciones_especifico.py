#!/usr/bin/env python3
"""
Script específico para separar direcciones con formato español específico
"""

import pandas as pd
import re
import os

def limpiar_texto(texto):
    """Limpia y normaliza el texto"""
    if pd.isna(texto):
        return ''
    return str(texto).strip()

def separar_direccion_especifica(direccion_completa):
    """
    Separa direcciones con formato específico español
    """
    if pd.isna(direccion_completa) or direccion_completa == '':
        return {
            'tipo_via': '',
            'nombre_via': '',
            'numero': '',
            'cp': '',
            'poblacion': '',
            'provincia': ''
        }
    
    direccion = limpiar_texto(direccion_completa)
    
    # Patrones específicos para tu formato
    cp_pattern = r'\b\d{5}\b'
    numero_pattern = r'\b\d{1,4}[A-Z]?\b'
    
    # Extraer CP
    cp_match = re.search(cp_pattern, direccion)
    cp = cp_match.group() if cp_match else ''
    
    # Extraer número
    numero_match = re.search(numero_pattern, direccion)
    numero = numero_match.group() if numero_match else ''
    
    # Tipos de vía específicos para tu formato
    tipos_via = {
        'CALLE': ['CL', 'CALLE', 'C/'],
        'AVENIDA': ['AV', 'AVENIDA', 'AVDA', 'AVDA.'],
        'PASEO': ['PS', 'PASEO', 'PSEO'],
        'PLAZA': ['PL', 'PLAZA'],
        'TRAVESÍA': ['TRV', 'TRAVESÍA', 'TRAV'],
        'CARRETERA': ['CTRA', 'CARRETERA'],
        'CAMINO': ['CM', 'CAMINO'],
        'RONDA': ['RDA', 'RONDA'],
        'BULEVAR': ['BLVD', 'BULEVAR'],
        'JARDINES': ['JARD', 'JARDINES'],
        'URBANIZACIÓN': ['URB', 'URBANIZACIÓN'],
        'POLÍGONO': ['POL', 'POLÍGONO'],
        'PARCELA': ['PARC', 'PARCELA'],
        'EDIFICIO': ['EDIF', 'EDIFICIO'],
        'TORRE': ['TORR', 'TORRE'],
        'BLOQUE': ['BLOQ', 'BLOQUE'],
        'PORTAL': ['PORT', 'PORTAL'],
        'ACCESO': ['ACCES', 'ACCESO'],
        'ZONA': ['ZZ', 'ZONA']
    }
    
    tipo_via = ''
    nombre_via = ''
    
    # Buscar tipo de vía al inicio
    for tipo_principal, variantes in tipos_via.items():
        for variante in variantes:
            if direccion.upper().startswith(variante):
                tipo_via = tipo_principal
                # Extraer nombre después del tipo
                nombre_inicio = len(variante)
                nombre_via = direccion[nombre_inicio:].strip()
                break
        if tipo_via:
            break
    
    # Limpiar nombre de la vía
    if nombre_via:
        # Remover número, CP y resto
        nombre_via = re.sub(r'\b\d{1,4}[A-Z]?\b.*', '', nombre_via).strip()
        nombre_via = re.sub(r'\b\d{5}\b.*', '', nombre_via).strip()
        nombre_via = nombre_via.rstrip(',').strip()
        nombre_via = nombre_via.rstrip('.').strip()
    
    # Extraer población y provincia usando el formato específico
    # Buscar patrones como "29120. Alhaurín de la Torre. Málaga."
    poblacion_provincia_pattern = r'(\d{5})\.\s*([^.]+)\.\s*([^.]+)\.?'
    match = re.search(poblacion_provincia_pattern, direccion)
    
    poblacion = ''
    provincia = ''
    
    if match:
        cp_encontrado, pob, prov = match.groups()
        poblacion = pob.strip()
        provincia = prov.strip()
    else:
        # Método alternativo: separar por puntos
        partes = [p.strip() for p in direccion.split('.')]
        if len(partes) >= 3:
            # Buscar la parte que contiene el CP
            for parte in partes:
                if re.search(cp_pattern, parte):
                    # La siguiente parte suele ser la población
                    idx = partes.index(parte)
                    if idx + 1 < len(partes):
                        poblacion = partes[idx + 1]
                    if idx + 2 < len(partes):
                        provincia = partes[idx + 2]
                    break
    
    return {
        'tipo_via': tipo_via,
        'nombre_via': nombre_via,
        'numero': numero,
        'cp': cp,
        'poblacion': poblacion,
        'provincia': provincia
    }

def procesar_excel_especifico(archivo_entrada, archivo_salida=None):
    """
    Procesa el archivo Excel con separación específica
    """
    try:
        print(f"📖 Leyendo archivo: {archivo_entrada}")
        df = pd.read_excel(archivo_entrada)
        
        print(f"📊 Filas encontradas: {len(df)}")
        print(f"📋 Columnas: {list(df.columns)}")
        
        if len(df.columns) < 2:
            print("❌ Error: Se necesitan al menos 2 columnas")
            return False
        
        columna_nombre = df.columns[0]
        columna_direccion = df.columns[1]
        
        print(f"🏢 Nombre: {columna_nombre}")
        print(f"📍 Dirección: {columna_direccion}")
        
        # Mostrar ejemplos
        print(f"\n📝 Ejemplos de datos:")
        for i in range(min(3, len(df))):
            print(f"   {i+1}. {df.iloc[i][columna_nombre]}")
            print(f"      {df.iloc[i][columna_direccion]}")
        
        print(f"\n🔄 Procesando...")
        
        datos_procesados = []
        errores = 0
        
        for index, row in df.iterrows():
            try:
                nombre = row[columna_nombre]
                direccion_completa = row[columna_direccion]
                
                componentes = separar_direccion_especifica(direccion_completa)
                
                datos_procesados.append({
                    'Nombre': nombre,
                    'Tipo_Via': componentes['tipo_via'],
                    'Nombre_Via': componentes['nombre_via'],
                    'Numero': componentes['numero'],
                    'CP': componentes['cp'],
                    'Poblacion': componentes['poblacion'],
                    'Provincia': componentes['provincia'],
                    'Direccion_Original': direccion_completa
                })
                
                if (index + 1) % 100 == 0:
                    print(f"   Procesadas {index + 1} filas...")
                    
            except Exception as e:
                errores += 1
                print(f"   Error en fila {index + 1}: {str(e)}")
        
        df_procesado = pd.DataFrame(datos_procesados)
        
        if archivo_salida is None:
            nombre_base = os.path.splitext(archivo_entrada)[0]
            archivo_salida = f"{nombre_base}_separado.xlsx"
        
        df_procesado.to_excel(archivo_salida, index=False)
        
        print(f"\n✅ Archivo guardado: {archivo_salida}")
        print(f"📊 Total procesadas: {len(df_procesado)}")
        print(f"❌ Errores: {errores}")
        
        # Estadísticas
        print(f"\n📈 Estadísticas:")
        tipos_via = df_procesado['Tipo_Via'].value_counts()
        print(f"   Tipos de vía más comunes:")
        for tipo, count in tipos_via.head(5).items():
            print(f"     {tipo}: {count}")
        
        provincias = df_procesado['Provincia'].value_counts()
        print(f"   Provincias más comunes:")
        for prov, count in provincias.head(5).items():
            print(f"     {prov}: {count}")
        
        # Ejemplo de resultado
        if len(df_procesado) > 0:
            print(f"\n📝 Ejemplo de resultado:")
            ejemplo = df_procesado.iloc[0]
            print(f"   Nombre: {ejemplo['Nombre']}")
            print(f"   Tipo: {ejemplo['Tipo_Via']}")
            print(f"   Vía: {ejemplo['Nombre_Via']}")
            print(f"   Número: {ejemplo['Numero']}")
            print(f"   CP: {ejemplo['CP']}")
            print(f"   Población: {ejemplo['Poblacion']}")
            print(f"   Provincia: {ejemplo['Provincia']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("🔧 Separador Específico de Direcciones Españolas")
    print("=" * 60)
    
    archivos_excel = [f for f in os.listdir('.') if f.endswith(('.xls', '.xlsx'))]
    
    if not archivos_excel:
        print("📁 No se encontraron archivos Excel")
        return
    
    print(f"📁 Archivos encontrados: {archivos_excel}")
    
    for archivo in archivos_excel:
        print(f"\n¿Procesar {archivo}? (s/n): ", end="")
        if input().lower() == 's':
            print(f"\n🔄 Procesando {archivo}...")
            if procesar_excel_especifico(archivo):
                print("✅ ¡Completado!")
                print(f"📁 El archivo procesado está listo para importar")
            break
    
    print(f"\n🎉 ¡Proceso terminado!")

if __name__ == "__main__":
    main()







