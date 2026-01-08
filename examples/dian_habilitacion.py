#!/usr/bin/env python3
# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
DIAN Facturacion Electronica - Script de Habilitacion

Este script implementa el proceso completo de habilitacion ante la DIAN,
soportando facturas, notas de credito y notas de debito.

Basado en implementacion funcional aprobada por DIAN.

USO:
    python dian_habilitacion.py --tipo factura     # Enviar factura
    python dian_habilitacion.py --tipo credito     # Enviar nota credito
    python dian_habilitacion.py --tipo debito      # Enviar nota debito
    python dian_habilitacion.py --lote             # Enviar lote completo (30F + 10NC + 10ND)
    python dian_habilitacion.py --verificar        # Verificar documentos pendientes
    python dian_habilitacion.py --status           # Ver estado de habilitacion
"""

import argparse
import io
import random
import zipfile
from datetime import datetime, timezone, timedelta

from lxml import etree

# Importar componentes de facho
from facho.fe.builders import (
    InvoiceBuilder,
    CreditNoteBuilder,
    DebitNoteBuilder,
    InvoiceConfig,
    InvoiceData,
    InvoiceLine,
    Party,
    Address,
    CreditNoteData,
    DebitNoteData,
    DOC_TYPES,
)
from facho.fe.client import (
    DianSimpleClient,
    DocumentTracker,
    TrackedDocument,
    calcular_cufe,
)
from facho.fe.signing import XAdESSigner


# =============================================================================
# CONFIGURACION - Modificar segun su empresa
# =============================================================================

CONFIG = {
    # Software DIAN
    'software_id': '1e3fa8f4-1a91-4028-9293-a9817406100f',
    'software_pin': '12345',
    'test_set_id': 'e9015851-e8e1-4cee-99cc-470044cded3e',

    # Certificado
    'cert_path': '/path/to/certificate.pfx',
    'cert_password': 'your_password',

    # Empresa
    'nit': '1001186599',
    'company_name': 'EMPRESA DE PRUEBA S.A.S',
    'technical_key': 'fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',

    # Resolucion
    'resolution_number': '18760000001',
    'resolution_date': '2019-01-19',
    'resolution_end_date': '2030-01-19',
    'prefix': 'SETP',
    'range_from': '990000000',
    'range_to': '995000000',

    # Cliente prueba (consumidor final)
    'customer_nit': '222222222222',

    # Ambiente: 1=Produccion, 2=Pruebas
    'environment': '2',

    # Archivo de tracking
    'tracking_file': '/tmp/dian_tracking.json',
}


# =============================================================================
# CONFIGURACION DE DIRECCIONES
# =============================================================================

DEFAULT_ADDRESS = Address(
    city_code='68081',
    city_name='Bucaramanga',
    postal_zone='680001',
    country_subentity='Santander',
    country_subentity_code='68',
    address_line='Calle 123 # 45-67',
    country_code='CO',
    country_name='Colombia'
)


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_invoice_config() -> InvoiceConfig:
    """Obtener configuracion de factura desde CONFIG."""
    return InvoiceConfig(
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
        environment=CONFIG['environment'],
    )


def get_supplier() -> Party:
    """Obtener datos del proveedor (emisor)."""
    return Party(
        nit=CONFIG['nit'],
        name=CONFIG['company_name'],
        legal_name=CONFIG['company_name'],
        organization_code='1',  # Persona juridica
        tax_level_code='R-99-PN',
        tax_scheme_code='01',
        tax_scheme_name='IVA',
        scheme_name='31',  # NIT
        address=DEFAULT_ADDRESS,
        email='empresa@test.com',
        responsability_regime_code='48',
    )


def get_customer() -> Party:
    """Obtener datos del cliente (consumidor final para pruebas)."""
    return Party(
        nit=CONFIG['customer_nit'],
        name='Consumidor Final',
        legal_name='Consumidor Final',
        organization_code='2',  # Persona natural
        tax_level_code='R-99-PN',
        tax_scheme_code='01',
        tax_scheme_name='IVA',
        scheme_name='13',  # Cedula
        address=DEFAULT_ADDRESS,
        email='cliente@test.com',
        responsability_regime_code='48',
    )


def get_random_lines() -> list:
    """Generar lineas de factura aleatorias para pruebas."""
    base_price = round(random.uniform(50000, 200000), 2)
    quantity = round(random.uniform(1, 5), 2)

    return [
        InvoiceLine(
            description='Producto de prueba',
            quantity=quantity,
            unit_code='94',  # Unidad
            unit_price=base_price,
            tax_percent=19.0,
            item_id='PROD001',
            item_scheme_id='999',
            item_scheme_name='Estandar de adopcion del contribuyente',
        )
    ]


def create_zip_file(xml_content: bytes, file_name: str) -> bytes:
    """Crear archivo ZIP con el XML."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(file_name, xml_content)
    return zip_buffer.getvalue()


# =============================================================================
# PROCESAMIENTO DE DOCUMENTOS
# =============================================================================

def process_invoice(
    config: InvoiceConfig,
    tracker: DocumentTracker,
    signer: XAdESSigner,
    client: DianSimpleClient,
    verify: bool = True
) -> dict:
    """
    Procesar y enviar una factura.

    Returns:
        Diccionario con el resultado
    """
    now = datetime.now(timezone(timedelta(hours=-5)))

    # Obtener consecutivo
    doc_number = tracker.get_next_document_number()

    # Datos de la factura
    invoice_data = InvoiceData(
        number=doc_number,
        issue_date=now.strftime('%Y-%m-%d'),
        issue_time=now.strftime('%H:%M:%S-05:00'),
        due_date=(now + timedelta(days=30)).strftime('%Y-%m-%d'),
        note='Factura electronica de prueba',
        supplier=get_supplier(),
        customer=get_customer(),
        lines=get_random_lines(),
    )

    # Calcular totales para el CUFE
    subtotal = sum(l.quantity * l.unit_price for l in invoice_data.lines)
    tax_iva = sum(l.quantity * l.unit_price * (l.tax_percent / 100) for l in invoice_data.lines)
    total = subtotal + tax_iva

    # Calcular CUFE
    cufe = calcular_cufe(
        numero=invoice_data.number,
        fecha_emision=invoice_data.issue_date,
        hora_emision=invoice_data.issue_time,
        subtotal=subtotal,
        iva=tax_iva,
        total=total,
        nit_emisor=config.nit,
        nit_adquiriente=invoice_data.customer.nit,
        clave_tecnica=config.technical_key,
        tipo_ambiente=config.environment
    )

    print(f"\n{'='*60}")
    print(f"  FACTURA: {doc_number}")
    print(f"{'='*60}")
    print(f"  CUFE: {cufe[:40]}...")
    print(f"  Total: ${total:,.2f} COP")

    # Construir XML
    print("  Construyendo XML...")
    builder = InvoiceBuilder(config)
    xml_doc = builder.build(invoice_data)

    # Firmar
    print("  Firmando documento...")
    signed_xml = signer.sign_xml(xml_doc)
    xml_bytes = etree.tostring(signed_xml, encoding='UTF-8', xml_declaration=True)

    # Crear ZIP
    xml_file_name = f"fv{doc_number}.xml"
    zip_file_name = f"fv{doc_number}.zip"
    zip_content = create_zip_file(xml_bytes, xml_file_name)

    # Enviar a DIAN
    print("  Enviando a DIAN...")
    result = client.send_and_verify(
        file_name=zip_file_name,
        content_file=zip_content,
        test_set_id=config.test_set_id,
        wait_seconds=10 if verify else 0,
        verify=verify
    )

    # Registrar en tracker
    tracked_doc = TrackedDocument(
        doc_type='factura',
        number=doc_number,
        uuid=cufe,
        issue_date=invoice_data.issue_date,
        issue_time=invoice_data.issue_time,
        total=total,
        zip_key=result.get('zip_key'),
        is_valid=result.get('is_valid'),
        status_code=result.get('status_response', {}).status_code if result.get('status_response') else None,
        status_description=result.get('status_response', {}).status_description if result.get('status_response') else None,
    )
    tracker.add_document(tracked_doc)

    # Mostrar resultado
    if result.get('zip_key'):
        print(f"  ZipKey: {result['zip_key']}")
    if result.get('is_valid') is True:
        print(f"  AUTORIZADA")
    elif result.get('is_valid') is False:
        status = result.get('status_response')
        print(f"  RECHAZADA: {status.status_description if status else 'Sin detalles'}")
    else:
        print(f"  Estado pendiente de verificacion")

    return {
        'doc_type': 'factura',
        'number': doc_number,
        'cufe': cufe,
        'total': total,
        'result': result,
    }


def process_credit_note(
    config: InvoiceConfig,
    tracker: DocumentTracker,
    signer: XAdESSigner,
    client: DianSimpleClient,
    ref_invoice: TrackedDocument,
    verify: bool = True
) -> dict:
    """
    Procesar y enviar una nota de credito.

    Args:
        ref_invoice: Factura de referencia

    Returns:
        Diccionario con el resultado
    """
    now = datetime.now(timezone(timedelta(hours=-5)))
    doc_number = tracker.get_next_document_number()

    # Datos de la nota credito
    credit_note_data = CreditNoteData(
        number=doc_number,
        issue_date=now.strftime('%Y-%m-%d'),
        issue_time=now.strftime('%H:%M:%S-05:00'),
        note='Nota credito de prueba',
        supplier=get_supplier(),
        customer=get_customer(),
        lines=get_random_lines(),
        billing_reference_id=ref_invoice.number,
        billing_reference_uuid=ref_invoice.uuid,
        billing_reference_date=ref_invoice.issue_date,
        discrepancy_response_code='2',  # Anulacion
        discrepancy_description='Anulacion de factura electronica',
    )

    subtotal = sum(l.quantity * l.unit_price for l in credit_note_data.lines)
    tax_iva = sum(l.quantity * l.unit_price * (l.tax_percent / 100) for l in credit_note_data.lines)
    total = subtotal + tax_iva

    print(f"\n{'='*60}")
    print(f"  NOTA CREDITO: {doc_number}")
    print(f"{'='*60}")
    print(f"  Referencia: {ref_invoice.number}")
    print(f"  Total: ${total:,.2f} COP")

    # Construir XML
    print("  Construyendo XML...")
    builder = CreditNoteBuilder(config)
    xml_doc = builder.build(credit_note_data)

    # Firmar
    print("  Firmando documento...")
    signed_xml = signer.sign_xml(xml_doc)
    xml_bytes = etree.tostring(signed_xml, encoding='UTF-8', xml_declaration=True)

    # Crear ZIP
    xml_file_name = f"nc{doc_number}.xml"
    zip_file_name = f"nc{doc_number}.zip"
    zip_content = create_zip_file(xml_bytes, xml_file_name)

    # Enviar a DIAN
    print("  Enviando a DIAN...")
    result = client.send_and_verify(
        file_name=zip_file_name,
        content_file=zip_content,
        test_set_id=config.test_set_id,
        wait_seconds=10 if verify else 0,
        verify=verify
    )

    # Obtener CUDE del documento (del builder)
    cude_el = xml_doc.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID')
    cude = cude_el.text if cude_el is not None else ''

    # Registrar en tracker
    tracked_doc = TrackedDocument(
        doc_type='credito',
        number=doc_number,
        uuid=cude,
        issue_date=credit_note_data.issue_date,
        issue_time=credit_note_data.issue_time,
        total=total,
        ref_invoice_number=ref_invoice.number,
        ref_invoice_uuid=ref_invoice.uuid,
        zip_key=result.get('zip_key'),
        is_valid=result.get('is_valid'),
    )
    tracker.add_document(tracked_doc)

    # Mostrar resultado
    if result.get('zip_key'):
        print(f"  ZipKey: {result['zip_key']}")
    if result.get('is_valid') is True:
        print(f"  AUTORIZADA")
    elif result.get('is_valid') is False:
        print(f"  RECHAZADA")
    else:
        print(f"  Estado pendiente de verificacion")

    return {
        'doc_type': 'credito',
        'number': doc_number,
        'cude': cude,
        'total': total,
        'result': result,
    }


def process_debit_note(
    config: InvoiceConfig,
    tracker: DocumentTracker,
    signer: XAdESSigner,
    client: DianSimpleClient,
    ref_invoice: TrackedDocument,
    verify: bool = True
) -> dict:
    """
    Procesar y enviar una nota de debito.

    Args:
        ref_invoice: Factura de referencia

    Returns:
        Diccionario con el resultado
    """
    now = datetime.now(timezone(timedelta(hours=-5)))
    doc_number = tracker.get_next_document_number()

    # Datos de la nota debito
    debit_note_data = DebitNoteData(
        number=doc_number,
        issue_date=now.strftime('%Y-%m-%d'),
        issue_time=now.strftime('%H:%M:%S-05:00'),
        note='Nota debito de prueba',
        supplier=get_supplier(),
        customer=get_customer(),
        lines=get_random_lines(),
        billing_reference_id=ref_invoice.number,
        billing_reference_uuid=ref_invoice.uuid,
        billing_reference_date=ref_invoice.issue_date,
        discrepancy_response_code='1',  # Intereses
        discrepancy_description='Intereses',
    )

    subtotal = sum(l.quantity * l.unit_price for l in debit_note_data.lines)
    tax_iva = sum(l.quantity * l.unit_price * (l.tax_percent / 100) for l in debit_note_data.lines)
    total = subtotal + tax_iva

    print(f"\n{'='*60}")
    print(f"  NOTA DEBITO: {doc_number}")
    print(f"{'='*60}")
    print(f"  Referencia: {ref_invoice.number}")
    print(f"  Total: ${total:,.2f} COP")

    # Construir XML
    print("  Construyendo XML...")
    builder = DebitNoteBuilder(config)
    xml_doc = builder.build(debit_note_data)

    # Firmar
    print("  Firmando documento...")
    signed_xml = signer.sign_xml(xml_doc)
    xml_bytes = etree.tostring(signed_xml, encoding='UTF-8', xml_declaration=True)

    # Crear ZIP
    xml_file_name = f"nd{doc_number}.xml"
    zip_file_name = f"nd{doc_number}.zip"
    zip_content = create_zip_file(xml_bytes, xml_file_name)

    # Enviar a DIAN
    print("  Enviando a DIAN...")
    result = client.send_and_verify(
        file_name=zip_file_name,
        content_file=zip_content,
        test_set_id=config.test_set_id,
        wait_seconds=10 if verify else 0,
        verify=verify
    )

    # Obtener CUDE del documento
    cude_el = xml_doc.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID')
    cude = cude_el.text if cude_el is not None else ''

    # Registrar en tracker
    tracked_doc = TrackedDocument(
        doc_type='debito',
        number=doc_number,
        uuid=cude,
        issue_date=debit_note_data.issue_date,
        issue_time=debit_note_data.issue_time,
        total=total,
        ref_invoice_number=ref_invoice.number,
        ref_invoice_uuid=ref_invoice.uuid,
        zip_key=result.get('zip_key'),
        is_valid=result.get('is_valid'),
    )
    tracker.add_document(tracked_doc)

    # Mostrar resultado
    if result.get('zip_key'):
        print(f"  ZipKey: {result['zip_key']}")
    if result.get('is_valid') is True:
        print(f"  AUTORIZADA")
    elif result.get('is_valid') is False:
        print(f"  RECHAZADA")
    else:
        print(f"  Estado pendiente de verificacion")

    return {
        'doc_type': 'debito',
        'number': doc_number,
        'cude': cude,
        'total': total,
        'result': result,
    }


# =============================================================================
# MODO LOTE
# =============================================================================

def run_batch_mode(
    config: InvoiceConfig,
    tracker: DocumentTracker,
    signer: XAdESSigner,
    client: DianSimpleClient
):
    """Ejecutar modo lote para completar habilitacion."""
    progress = tracker.get_habilitacion_progress()

    print("\n" + "="*70)
    print("  MODO LOTE - Completar habilitacion DIAN")
    print("="*70)
    print(f"  Facturas:      {progress['facturas']['completadas']}/{progress['facturas']['requeridas']}")
    print(f"  Notas Credito: {progress['notas_credito']['completadas']}/{progress['notas_credito']['requeridas']}")
    print(f"  Notas Debito:  {progress['notas_debito']['completadas']}/{progress['notas_debito']['requeridas']}")
    print("="*70)

    if progress['habilitacion_completa']:
        print("\n  Habilitacion ya esta completa!")
        return

    # Enviar facturas faltantes
    facturas_needed = progress['facturas']['faltantes']
    if facturas_needed > 0:
        print(f"\n  Enviando {facturas_needed} facturas...")
        for i in range(facturas_needed):
            process_invoice(config, tracker, signer, client, verify=True)

    # Obtener facturas para referenciar en notas
    invoices = tracker.get_invoices()
    valid_invoices = [inv for inv in invoices if inv.is_valid is True]

    # Enviar notas credito faltantes
    creditos_needed = progress['notas_credito']['faltantes']
    if creditos_needed > 0:
        print(f"\n  Enviando {creditos_needed} notas de credito...")
        for i in range(min(creditos_needed, len(valid_invoices))):
            ref_invoice = valid_invoices[i % len(valid_invoices)]
            process_credit_note(config, tracker, signer, client, ref_invoice, verify=True)

    # Enviar notas debito faltantes
    debitos_needed = progress['notas_debito']['faltantes']
    if debitos_needed > 0:
        print(f"\n  Enviando {debitos_needed} notas de debito...")
        for i in range(min(debitos_needed, len(valid_invoices))):
            ref_invoice = valid_invoices[i % len(valid_invoices)]
            process_debit_note(config, tracker, signer, client, ref_invoice, verify=True)

    # Resumen final
    final_progress = tracker.get_habilitacion_progress()
    print("\n" + "="*70)
    print("  RESUMEN FINAL")
    print("="*70)
    print(f"  Facturas:      {final_progress['facturas']['completadas']}/{final_progress['facturas']['requeridas']}")
    print(f"  Notas Credito: {final_progress['notas_credito']['completadas']}/{final_progress['notas_credito']['requeridas']}")
    print(f"  Notas Debito:  {final_progress['notas_debito']['completadas']}/{final_progress['notas_debito']['requeridas']}")
    print("="*70)

    if final_progress['habilitacion_completa']:
        print("\n  HABILITACION COMPLETA!")
    else:
        print("\n  Habilitacion aun pendiente. Ejecute nuevamente para completar.")


# =============================================================================
# VERIFICACION DE PENDIENTES
# =============================================================================

def verify_pending_documents(tracker: DocumentTracker, client: DianSimpleClient):
    """Verificar estado de documentos pendientes."""
    pending = tracker.get_pending_documents()

    if not pending:
        print("\n  No hay documentos pendientes de verificacion.")
        return

    print(f"\n  Verificando {len(pending)} documentos pendientes...")

    for doc in pending:
        print(f"\n  {doc.doc_type.upper()}: {doc.number}")
        response = client.get_status_zip(doc.zip_key)

        tracker.update_status(
            document_number=doc.number,
            is_valid=response.is_valid,
            status_code=response.status_code,
            status_description=response.status_description
        )

        if response.is_valid:
            print(f"    AUTORIZADO")
        elif response.is_valid is False:
            print(f"    RECHAZADO: {response.status_description}")
        else:
            print(f"    Estado desconocido")


def show_status(tracker: DocumentTracker):
    """Mostrar estado actual del tracking."""
    summary = tracker.get_summary()
    progress = tracker.get_habilitacion_progress()

    print("\n" + "="*70)
    print("  ESTADO DE HABILITACION")
    print("="*70)
    print(f"  NIT: {summary['nit']}")
    print(f"  Prefijo: {summary['prefix']}")
    print(f"  Ultimo consecutivo: {summary['ultimo_consecutivo']}")
    print()
    print(f"  DOCUMENTOS:")
    print(f"    Facturas:      {progress['facturas']['completadas']}/{progress['facturas']['requeridas']}")
    print(f"    Notas Credito: {progress['notas_credito']['completadas']}/{progress['notas_credito']['requeridas']}")
    print(f"    Notas Debito:  {progress['notas_debito']['completadas']}/{progress['notas_debito']['requeridas']}")
    print()
    print(f"  ESTADISTICAS:")
    print(f"    Total documentos: {summary['total_documentos']}")
    print(f"    Validados:        {summary['validados']}")
    print(f"    Rechazados:       {summary['rechazados']}")
    print(f"    Pendientes:       {summary['pendientes']}")
    print("="*70)

    if progress['habilitacion_completa']:
        print("\n  HABILITACION COMPLETA!")
    else:
        print("\n  Habilitacion pendiente.")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='DIAN Facturacion Electronica - Habilitacion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python dian_habilitacion.py --tipo factura     # Enviar una factura
    python dian_habilitacion.py --tipo credito     # Enviar nota credito
    python dian_habilitacion.py --tipo debito      # Enviar nota debito
    python dian_habilitacion.py --lote             # Completar habilitacion
    python dian_habilitacion.py --verificar        # Verificar pendientes
    python dian_habilitacion.py --status           # Ver estado actual
        """
    )
    parser.add_argument(
        '--tipo',
        choices=['factura', 'credito', 'debito'],
        help='Tipo de documento a enviar'
    )
    parser.add_argument(
        '--lote',
        action='store_true',
        help='Enviar lote completo para habilitacion'
    )
    parser.add_argument(
        '--verificar',
        action='store_true',
        help='Verificar estado de documentos pendientes'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Mostrar estado actual de habilitacion'
    )
    parser.add_argument(
        '--cert',
        help='Ruta al certificado .pfx/.p12'
    )
    parser.add_argument(
        '--password',
        help='Contrasena del certificado'
    )

    args = parser.parse_args()

    # Actualizar config con argumentos
    if args.cert:
        CONFIG['cert_path'] = args.cert
    if args.password:
        CONFIG['cert_password'] = args.password

    print("="*70)
    print("  DIAN Facturacion Electronica - Habilitacion")
    print("  Soporta: Facturas, Notas Credito, Notas Debito")
    print("="*70)

    # Inicializar tracker
    tracker = DocumentTracker(CONFIG['tracking_file'])
    tracker.set_config(
        prefix=CONFIG['prefix'],
        nit=CONFIG['nit'],
        start_consecutive=int(CONFIG['range_from'])
    )

    # Si solo se pide estado
    if args.status:
        show_status(tracker)
        return

    # Cargar certificado y cliente
    print("\n[1] Cargando certificado...")
    try:
        signer = XAdESSigner.from_pkcs12(CONFIG['cert_path'], CONFIG['cert_password'])
        client = DianSimpleClient(
            certificate_path=CONFIG['cert_path'],
            certificate_password=CONFIG['cert_password'],
            environment='habilitacion' if CONFIG['environment'] == '2' else 'produccion'
        )
        print(f"    Certificado cargado correctamente")
    except Exception as e:
        print(f"    Error cargando certificado: {e}")
        print("    Use --cert y --password para especificar el certificado")
        return

    # Configuracion de factura
    config = get_invoice_config()

    # Modo verificar
    if args.verificar:
        verify_pending_documents(tracker, client)
        return

    # Modo lote
    if args.lote:
        run_batch_mode(config, tracker, signer, client)
        return

    # Documento individual
    if args.tipo:
        if args.tipo == 'factura':
            process_invoice(config, tracker, signer, client)
        elif args.tipo in ['credito', 'debito']:
            # Necesitamos una factura de referencia
            invoices = tracker.get_invoices()
            valid_invoices = [inv for inv in invoices if inv.is_valid is True]

            if not valid_invoices:
                print("\n  Error: Se necesita al menos una factura validada para crear notas")
                print("  Primero ejecute: python dian_habilitacion.py --tipo factura")
                return

            ref_invoice = valid_invoices[-1]  # Usar la ultima factura

            if args.tipo == 'credito':
                process_credit_note(config, tracker, signer, client, ref_invoice)
            else:
                process_debit_note(config, tracker, signer, client, ref_invoice)
    else:
        # Sin argumentos, mostrar estado
        parser.print_help()
        print()
        show_status(tracker)


if __name__ == '__main__':
    main()
