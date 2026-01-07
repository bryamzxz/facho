#!/usr/bin/env python3
"""
Ejemplo de factura electronica DIAN usando la implementacion simplificada.

Este ejemplo muestra como generar una factura electronica valida para DIAN
usando los nuevos modulos de facho basados en la implementacion funcional.

IMPORTANTE: Antes de usar, configure los siguientes parametros con sus datos reales:

1. Software DIAN:
   - software_id: ID del software registrado en DIAN
   - software_pin: PIN del software
   - test_set_id: ID del set de pruebas (solo para habilitacion)
   - technical_key: Clave tecnica de la resolucion

2. Certificado:
   - cert_path: Ruta al archivo .pfx o .p12
   - cert_password: Contrasena del certificado

3. Empresa:
   - nit: NIT de la empresa sin digito de verificacion
   - company_name: Nombre o razon social

4. Resolucion:
   - resolution_number: Numero de resolucion DIAN
   - resolution_date: Fecha inicio vigencia (YYYY-MM-DD)
   - resolution_end_date: Fecha fin vigencia (YYYY-MM-DD)
   - prefix: Prefijo autorizado
   - range_from: Numero inicial del rango
   - range_to: Numero final del rango

Uso:
    python dian_invoice_simple.py
"""

import os
import sys
import random
import zipfile
import io
import time
from datetime import datetime, timezone, timedelta

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lxml import etree

from facho.fe.builders import InvoiceBuilder
from facho.fe.builders.invoice_builder import (
    InvoiceConfig,
    InvoiceData,
    InvoiceLine,
    Party,
    Address
)
from facho.fe.signing import XAdESSigner
from facho.fe.client.dian_simple import DianSimpleClient


# =============================================================================
# CONFIGURACION - REEMPLAZAR CON SUS DATOS REALES
# =============================================================================

CONFIG = {
    # Software DIAN - Obtener en el portal de habilitacion DIAN
    'software_id': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',  # UUID del software
    'software_pin': '12345',  # PIN numerico de 5 digitos
    'test_set_id': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',  # UUID del set de pruebas

    # Certificado digital - Archivo .pfx o .p12
    'cert_path': '/ruta/a/su/Certificado.pfx',
    'cert_password': 'su_contrasena_aqui',

    # Empresa emisora
    'nit': '900123456',  # NIT sin digito de verificacion
    'company_name': 'MI EMPRESA S.A.S.',
    'technical_key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',  # Clave tecnica de resolucion

    # Resolucion de facturacion
    'resolution_number': '18760000001',
    'resolution_date': '2024-01-01',
    'resolution_end_date': '2025-12-31',
    'prefix': 'FE',
    'range_from': '1',
    'range_to': '1000000',

    # Ambiente: '1' = Produccion, '2' = Pruebas/Habilitacion
    'environment': '2',
}

# Direccion del emisor
SUPPLIER_ADDRESS = Address(
    city_code='11001',
    city_name='Bogota',
    postal_zone='110111',
    country_subentity='Bogota D.C.',
    country_subentity_code='11',
    address_line='Carrera 10 # 20-30',
    country_code='CO',
    country_name='Colombia'
)

# Direccion del cliente
CUSTOMER_ADDRESS = Address(
    city_code='05001',
    city_name='Medellin',
    postal_zone='050001',
    country_subentity='Antioquia',
    country_subentity_code='05',
    address_line='Calle 50 # 40-20',
    country_code='CO',
    country_name='Colombia'
)


def validar_configuracion():
    """Validar que la configuracion tiene valores reales."""
    errores = []

    if 'xxxx' in CONFIG['software_id']:
        errores.append("- software_id: Debe configurar el ID del software DIAN")

    if 'xxxx' in CONFIG['test_set_id']:
        errores.append("- test_set_id: Debe configurar el ID del set de pruebas")

    if not os.path.exists(CONFIG['cert_path']):
        errores.append(f"- cert_path: El archivo no existe: {CONFIG['cert_path']}")

    if 'xxxx' in CONFIG['technical_key']:
        errores.append("- technical_key: Debe configurar la clave tecnica")

    if errores:
        print("=" * 70)
        print("ERROR: Configuracion incompleta")
        print("=" * 70)
        print("\nAntes de ejecutar, configure los siguientes parametros:\n")
        for error in errores:
            print(error)
        print("\nEdite este archivo y complete la seccion CONFIG con sus datos.")
        print("=" * 70)
        return False

    return True


def generar_factura():
    """Generar factura electronica de ejemplo."""

    print("=" * 70)
    print("  FACHO - Factura Electronica DIAN")
    print("=" * 70)

    # Validar configuracion
    if not validar_configuracion():
        return

    # Crear configuracion
    invoice_config = InvoiceConfig(
        software_id=CONFIG['software_id'],
        software_pin=CONFIG['software_pin'],
        technical_key=CONFIG['technical_key'],
        test_set_id=CONFIG['test_set_id'],
        nit=CONFIG['nit'],
        company_name=CONFIG['company_name'],
        resolution_number=CONFIG['resolution_number'],
        resolution_date=CONFIG['resolution_date'],
        resolution_end_date=CONFIG['resolution_end_date'],
        prefix=CONFIG['prefix'],
        range_from=CONFIG['range_from'],
        range_to=CONFIG['range_to'],
        environment=CONFIG['environment']
    )

    # Datos del proveedor (emisor)
    supplier = Party(
        nit=CONFIG['nit'],
        name=CONFIG['company_name'],
        legal_name=CONFIG['company_name'],
        organization_code='1',  # Persona Juridica
        tax_level_code='O-07;O-09',  # Responsable de IVA
        address=SUPPLIER_ADDRESS,
        email='facturacion@miempresa.com',
        responsability_regime_code='48'  # Regimen IVA
    )

    # Datos del cliente
    customer = Party(
        nit='900987654',  # NIT del cliente
        name='CLIENTE EJEMPLO S.A.',
        legal_name='CLIENTE EJEMPLO S.A.',
        organization_code='1',  # Persona Juridica
        tax_level_code='R-99-PN',  # No responsable
        scheme_name='31',  # NIT
        address=CUSTOMER_ADDRESS,
        email='cliente@ejemplo.com',
        responsability_regime_code='49'  # No responsable IVA
    )

    # Generar numero de factura
    numero = f"{CONFIG['prefix']}{random.randint(1, 999999):06d}"
    now = datetime.now(timezone(timedelta(hours=-5)))

    # Datos de la factura
    invoice_data = InvoiceData(
        number=numero,
        issue_date=now.strftime('%Y-%m-%d'),
        issue_time=now.strftime('%H:%M:%S-05:00'),
        due_date=now.strftime('%Y-%m-%d'),
        note='Factura electronica de prueba generada con Facho',
        supplier=supplier,
        customer=customer,
        lines=[
            InvoiceLine(
                description='Servicio de consultoria',
                quantity=1.0,
                unit_code='E48',  # Unidad de servicio
                unit_price=500000.00,
                tax_percent=19.0,
                item_id='SERV001'
            ),
            InvoiceLine(
                description='Producto de prueba',
                quantity=2.0,
                unit_code='94',  # Unidad
                unit_price=150000.00,
                tax_percent=19.0,
                item_id='PROD001'
            )
        ]
    )

    print(f"\n[1] Generando factura {numero}...")

    # Construir XML
    builder = InvoiceBuilder(invoice_config)
    invoice_xml = builder.build(invoice_data)

    print(f"    - Fecha: {invoice_data.issue_date}")
    print(f"    - Hora: {invoice_data.issue_time}")
    print(f"    - Cliente: {customer.name}")

    # Firmar XML
    print("\n[2] Firmando documento...")
    signer = XAdESSigner.from_pkcs12(
        CONFIG['cert_path'],
        CONFIG['cert_password']
    )
    signed_xml = signer.sign(invoice_xml)

    # Serializar XML
    xml_bytes = etree.tostring(
        signed_xml,
        encoding='UTF-8',
        xml_declaration=True
    )

    # Guardar XML para revision
    xml_path = f'/tmp/factura_{numero}.xml'
    with open(xml_path, 'wb') as f:
        f.write(xml_bytes)
    print(f"    - XML guardado: {xml_path}")

    # Crear ZIP
    print("\n[3] Creando archivo ZIP...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f'fv{numero}.xml', xml_bytes)
    zip_data = zip_buffer.getvalue()

    zip_path = f'/tmp/fv{numero}.zip'
    with open(zip_path, 'wb') as f:
        f.write(zip_data)
    print(f"    - ZIP guardado: {zip_path}")

    # Enviar a DIAN
    print("\n[4] Enviando a DIAN...")
    client = DianSimpleClient(
        certificate_path=CONFIG['cert_path'],
        certificate_password=CONFIG['cert_password'],
        environment='habilitacion'
    )

    response = client.send_test_set_async(
        file_name=f'fv{numero}.zip',
        content_file=zip_data,
        test_set_id=CONFIG['test_set_id']
    )

    if response.zip_key:
        print(f"    - ZipKey: {response.zip_key}")

        # Esperar procesamiento
        print("\n[5] Esperando procesamiento DIAN (20 segundos)...")
        time.sleep(20)

        # Consultar estado
        print("\n[6] Consultando estado...")
        status = client.get_status_zip(response.zip_key)

        print("\n" + "=" * 70)
        print("RESULTADO")
        print("=" * 70)
        print(f"IsValid: {status.is_valid}")
        print(f"StatusCode: {status.status_code}")
        print(f"StatusDescription: {status.status_description}")

        if status.status_message:
            print(f"Mensaje: {status.status_message}")

        if status.error_messages:
            print("Errores:")
            for err in status.error_messages:
                print(f"  - {err}")

    else:
        print("    - ERROR: No se obtuvo ZipKey")
        if response.error_messages:
            print("Errores:")
            for err in response.error_messages:
                print(f"  - {err}")
        print("\nRespuesta completa:")
        print(response.xml_response[:2000] if response.xml_response else "Sin respuesta")

    print("\n" + "=" * 70)
    print("FIN")
    print("=" * 70)


if __name__ == '__main__':
    generar_factura()
