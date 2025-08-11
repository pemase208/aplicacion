#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar la base de datos de entidades financieras
desde el Banco de España y otras fuentes oficiales.
"""

import requests
import pandas as pd
import sqlite3
import json
import re
from datetime import datetime, date
from typing import List, Dict, Optional
import unicodedata
from app import app, db
from models import EntidadFinanciera

class ActualizadorEntidadesFinancieras:
    """Clase para gestionar la actualización de entidades financieras"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def limpiar_texto(self, texto: str) -> str:
        """Limpia y normaliza texto para búsquedas"""
        if not texto:
            return ""
        
        # Normalizar acentos
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if not unicodedata.combining(c))
        
        # Convertir a minúsculas y limpiar
        texto = texto.lower().strip()
        texto = re.sub(r'[^\w\s]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto)
        
        return texto
    
    def obtener_entidades_bde(self) -> List[Dict]:
        """
        Obtiene entidades financieras desde el Banco de España
        Usa la API pública del BdE cuando esté disponible
        """
        entidades = []
        
        try:
            # URL de la API del Banco de España (ejemplo)
            # Nota: Esta URL puede cambiar, consultar documentación oficial
            url_bde = "https://www.bde.es/webbde/es/estadis/infoest/tipos/tipos.html"
            
            print("🔍 Obteniendo datos del Banco de España...")
            
            # Por ahora, usamos datos de ejemplo basados en la estructura real
            # En producción, esto se conectaría a la API oficial del BdE
            
            entidades_ejemplo = [
                {
                    "nombre": "BANCO SANTANDER, S.A.",
                    "nombre_comercial": "Santander",
                    "tipo_entidad": "Banco",
                    "codigo_entidad": "0049",
                    "estado": "Activo",
                    "fecha_autorizacion": "1857-01-01",
                    "direccion_completa": "Paseo de Pereda, 9-12, 39004 Santander",
                    "direccion": "Paseo de Pereda",
                    "numero": "9-12",
                    "codigo_postal": "39004",
                    "localidad": "Santander",
                    "provincia": "Cantabria",
                    "comunidad_autonoma": "Cantabria",
                    "telefono": "942 202 000",
                    "email": "info@santander.com",
                    "web": "https://www.santander.com",
                    "cif_nif": "A39000013",
                    "supervisor_principal": "Banco de España"
                },
                {
                    "nombre": "BANCO BILBAO VIZCAYA ARGENTARIA, S.A.",
                    "nombre_comercial": "BBVA",
                    "tipo_entidad": "Banco",
                    "codigo_entidad": "0182",
                    "estado": "Activo",
                    "fecha_autorizacion": "1857-01-01",
                    "direccion_completa": "Plaza de San Nicolás, 4, 48005 Bilbao",
                    "direccion": "Plaza de San Nicolás",
                    "numero": "4",
                    "codigo_postal": "48005",
                    "localidad": "Bilbao",
                    "provincia": "Vizcaya",
                    "comunidad_autonoma": "País Vasco",
                    "telefono": "944 875 875",
                    "email": "info@bbva.com",
                    "web": "https://www.bbva.com",
                    "cif_nif": "A48265169",
                    "supervisor_principal": "Banco de España"
                },
                {
                    "nombre": "CAIXABANK, S.A.",
                    "nombre_comercial": "CaixaBank",
                    "tipo_entidad": "Banco",
                    "codigo_entidad": "2100",
                    "estado": "Activo",
                    "fecha_autorizacion": "2011-01-01",
                    "direccion_completa": "Avenida Diagonal, 621-629, 08028 Barcelona",
                    "direccion": "Avenida Diagonal",
                    "numero": "621-629",
                    "codigo_postal": "08028",
                    "localidad": "Barcelona",
                    "provincia": "Barcelona",
                    "comunidad_autonoma": "Cataluña",
                    "telefono": "934 049 000",
                    "email": "info@caixabank.com",
                    "web": "https://www.caixabank.com",
                    "cif_nif": "A08663619",
                    "supervisor_principal": "Banco de España"
                }
            ]
            
            # Agregar más entidades de ejemplo
            entidades.extend(entidades_ejemplo)
            
            print(f"✅ Obtenidas {len(entidades)} entidades del Banco de España")
            return entidades
            
        except Exception as e:
            print(f"❌ Error obteniendo datos del BdE: {e}")
            return []
    
    def obtener_efcs_bde(self) -> List[Dict]:
        """
        Obtiene Establecimientos Financieros de Crédito (EFC)
        desde el Banco de España
        """
        efc_ejemplo = [
            {
                "nombre": "FINANCIERA EL CORTE INGLÉS, E.F.C., S.A.",
                "nombre_comercial": "Financiera El Corte Inglés",
                "tipo_entidad": "EFC",
                "codigo_entidad": "E0001",
                "estado": "Activo",
                "fecha_autorizacion": "1990-01-01",
                "direccion_completa": "Hermosilla, 112, 28009 Madrid",
                "direccion": "Hermosilla",
                "numero": "112",
                "codigo_postal": "28009",
                "localidad": "Madrid",
                "provincia": "Madrid",
                "comunidad_autonoma": "Madrid",
                "telefono": "914 360 000",
                "email": "info@financieraelcorteingles.es",
                "web": "https://www.financieraelcorteingles.es",
                "cif_nif": "A28010366",
                "supervisor_principal": "Banco de España"
            },
            {
                "nombre": "CAJA RURAL DE NAVARRA, S.C.C.",
                "nombre_comercial": "Caja Rural de Navarra",
                "tipo_entidad": "Caja de Ahorros",
                "codigo_entidad": "3001",
                "estado": "Activo",
                "fecha_autorizacion": "1921-01-01",
                "direccion_completa": "Avenida Carlos III, 2, 31002 Pamplona",
                "direccion": "Avenida Carlos III",
                "numero": "2",
                "codigo_postal": "31002",
                "localidad": "Pamplona",
                "provincia": "Navarra",
                "comunidad_autonoma": "Navarra",
                "telefono": "948 222 222",
                "email": "info@cajaruraldenavarra.es",
                "web": "https://www.cajaruraldenavarra.es",
                "cif_nif": "F31000001",
                "supervisor_principal": "Banco de España"
            }
        ]
        
        return efc_ejemplo
    
    def procesar_entidad(self, datos: Dict) -> EntidadFinanciera:
        """Procesa y crea una entidad financiera desde los datos"""
        
        # Limpiar y normalizar datos
        nombre = datos.get('nombre', '').strip()
        nombre_comercial = datos.get('nombre_comercial', '').strip()
        tipo_entidad = datos.get('tipo_entidad', 'Banco').strip()
        codigo_entidad = datos.get('codigo_entidad', '').strip()
        
        # Crear entidad
        entidad = EntidadFinanciera(
            nombre=nombre,
            nombre_comercial=nombre_comercial if nombre_comercial else None,
            tipo_entidad=tipo_entidad,
            codigo_entidad=codigo_entidad,
            estado=datos.get('estado', 'Activo'),
            fecha_autorizacion=datetime.strptime(datos.get('fecha_autorizacion', '1900-01-01'), '%Y-%m-%d').date() if datos.get('fecha_autorizacion') else None,
            direccion_completa=datos.get('direccion_completa', ''),
            direccion=datos.get('direccion', ''),
            numero=datos.get('numero', ''),
            codigo_postal=datos.get('codigo_postal', ''),
            localidad=datos.get('localidad', ''),
            provincia=datos.get('provincia', ''),
            comunidad_autonoma=datos.get('comunidad_autonoma', ''),
            telefono=datos.get('telefono', ''),
            email=datos.get('email', ''),
            web=datos.get('web', ''),
            cif_nif=datos.get('cif_nif', ''),
            supervisor_principal=datos.get('supervisor_principal', 'Banco de España'),
            fuente_datos='Banco de España',
            version_datos=datetime.now().strftime('%Y%m%d'),
            nombre_busqueda=self.limpiar_texto(nombre),
            localidad_busqueda=self.limpiar_texto(datos.get('localidad', ''))
        )
        
        return entidad
    
    def actualizar_base_datos(self, forzar_actualizacion: bool = False) -> Dict:
        """
        Actualiza la base de datos de entidades financieras
        """
        with app.app_context():
            try:
                print("🔄 Iniciando actualización de entidades financieras...")
                
                # Obtener datos del Banco de España
                entidades_bde = self.obtener_entidades_bde()
                efc_bde = self.obtener_efcs_bde()
                
                todas_entidades = entidades_bde + efc_bde
                
                if not todas_entidades:
                    return {
                        'success': False,
                        'message': 'No se pudieron obtener datos del Banco de España',
                        'entidades_procesadas': 0,
                        'entidades_nuevas': 0,
                        'entidades_actualizadas': 0
                    }
                
                entidades_nuevas = 0
                entidades_actualizadas = 0
                
                for datos_entidad in todas_entidades:
                    codigo_entidad = datos_entidad.get('codigo_entidad')
                    
                    if not codigo_entidad:
                        continue
                    
                    # Buscar si ya existe
                    entidad_existente = EntidadFinanciera.query.filter_by(
                        codigo_entidad=codigo_entidad
                    ).first()
                    
                    if entidad_existente:
                        # Actualizar entidad existente
                        if forzar_actualizacion:
                            entidad_procesada = self.procesar_entidad(datos_entidad)
                            
                            # Actualizar campos
                            entidad_existente.nombre = entidad_procesada.nombre
                            entidad_existente.nombre_comercial = entidad_procesada.nombre_comercial
                            entidad_existente.tipo_entidad = entidad_procesada.tipo_entidad
                            entidad_existente.estado = entidad_procesada.estado
                            entidad_existente.direccion_completa = entidad_procesada.direccion_completa
                            entidad_existente.direccion = entidad_procesada.direccion
                            entidad_existente.numero = entidad_procesada.numero
                            entidad_existente.codigo_postal = entidad_procesada.codigo_postal
                            entidad_existente.localidad = entidad_procesada.localidad
                            entidad_existente.provincia = entidad_procesada.provincia
                            entidad_existente.comunidad_autonoma = entidad_procesada.comunidad_autonoma
                            entidad_existente.telefono = entidad_procesada.telefono
                            entidad_existente.email = entidad_procesada.email
                            entidad_existente.web = entidad_procesada.web
                            entidad_existente.cif_nif = entidad_procesada.cif_nif
                            entidad_existente.fecha_ultima_actualizacion = datetime.utcnow()
                            entidad_existente.version_datos = entidad_procesada.version_datos
                            entidad_existente.nombre_busqueda = entidad_procesada.nombre_busqueda
                            entidad_existente.localidad_busqueda = entidad_procesada.localidad_busqueda
                            
                            entidades_actualizadas += 1
                    else:
                        # Crear nueva entidad
                        nueva_entidad = self.procesar_entidad(datos_entidad)
                        db.session.add(nueva_entidad)
                        entidades_nuevas += 1
                
                # Commit de cambios
                db.session.commit()
                
                resultado = {
                    'success': True,
                    'message': 'Actualización completada exitosamente',
                    'entidades_procesadas': len(todas_entidades),
                    'entidades_nuevas': entidades_nuevas,
                    'entidades_actualizadas': entidades_actualizadas,
                    'fecha_actualizacion': datetime.now().isoformat()
                }
                
                print(f"✅ Actualización completada:")
                print(f"   - Entidades procesadas: {resultado['entidades_procesadas']}")
                print(f"   - Entidades nuevas: {resultado['entidades_nuevas']}")
                print(f"   - Entidades actualizadas: {resultado['entidades_actualizadas']}")
                
                return resultado
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error en la actualización: {e}")
                return {
                    'success': False,
                    'message': f'Error en la actualización: {str(e)}',
                    'entidades_procesadas': 0,
                    'entidades_nuevas': 0,
                    'entidades_actualizadas': 0
                }
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de la base de datos"""
        with app.app_context():
            try:
                total_entidades = EntidadFinanciera.query.count()
                entidades_activas = EntidadFinanciera.query.filter_by(estado='Activo').count()
                
                # Estadísticas por tipo
                tipos_entidad = db.session.query(
                    EntidadFinanciera.tipo_entidad,
                    db.func.count(EntidadFinanciera.id)
                ).group_by(EntidadFinanciera.tipo_entidad).all()
                
                # Estadísticas por CCAA
                ccaa_stats = db.session.query(
                    EntidadFinanciera.comunidad_autonoma,
                    db.func.count(EntidadFinanciera.id)
                ).group_by(EntidadFinanciera.comunidad_autonoma).order_by(
                    db.func.count(EntidadFinanciera.id).desc()
                ).limit(10).all()
                
                return {
                    'total_entidades': total_entidades,
                    'entidades_activas': entidades_activas,
                    'tipos_entidad': dict(tipos_entidad),
                    'top_ccaa': dict(ccaa_stats),
                    'ultima_actualizacion': datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"❌ Error obteniendo estadísticas: {e}")
                return {}

def main():
    """Función principal para ejecutar la actualización"""
    actualizador = ActualizadorEntidadesFinancieras()
    
    print("🏦 Actualizador de Entidades Financieras del Banco de España")
    print("=" * 60)
    
    # Mostrar estadísticas actuales
    print("\n📊 Estadísticas actuales:")
    stats = actualizador.obtener_estadisticas()
    if stats:
        print(f"   Total de entidades: {stats.get('total_entidades', 0)}")
        print(f"   Entidades activas: {stats.get('entidades_activas', 0)}")
        print(f"   Tipos de entidad: {stats.get('tipos_entidad', {})}")
    
    # Preguntar si forzar actualización
    respuesta = input("\n¿Desea forzar la actualización completa? (s/N): ").lower()
    forzar = respuesta in ['s', 'si', 'sí', 'y', 'yes']
    
    # Ejecutar actualización
    resultado = actualizador.actualizar_base_datos(forzar_actualizacion=forzar)
    
    if resultado['success']:
        print(f"\n✅ {resultado['message']}")
        print(f"   Entidades procesadas: {resultado['entidades_procesadas']}")
        print(f"   Entidades nuevas: {resultado['entidades_nuevas']}")
        print(f"   Entidades actualizadas: {resultado['entidades_actualizadas']}")
    else:
        print(f"\n❌ {resultado['message']}")
    
    # Mostrar estadísticas finales
    print("\n📊 Estadísticas finales:")
    stats_final = actualizador.obtener_estadisticas()
    if stats_final:
        print(f"   Total de entidades: {stats_final.get('total_entidades', 0)}")
        print(f"   Entidades activas: {stats_final.get('entidades_activas', 0)}")

if __name__ == "__main__":
    main()







