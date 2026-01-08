#!/usr/bin/env python3
# This file is part of dian_fe.
"""
Interfaz de linea de comandos para DIAN Facturacion Electronica.
"""

import argparse
import json
import sys
import io
import zipfile
from datetime import datetime, timezone, timedelta

from lxml import etree


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description='DIAN Facturacion Electronica - CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  python -m dian_fe --tipo factura --config config.json
  python -m dian_fe --lote --config config.json
  python -m dian_fe --status <zipkey>
  python -m dian_fe --verificar
        '''
    )

    parser.add_argument(
        '--tipo',
        choices=['factura', 'credito', 'debito'],
        help='Tipo de documento a generar'
    )
    parser.add_argument(
        '--lote',
        action='store_true',
        help='Enviar lote completo de habilitacion (30 facturas, 10 NC, 10 ND)'
    )
    parser.add_argument(
        '--verificar',
        action='store_true',
        help='Verificar estado de documentos pendientes'
    )
    parser.add_argument(
        '--status',
        metavar='ZIPKEY',
        help='Consultar estado por ZipKey'
    )
    parser.add_argument(
        '--config',
        metavar='FILE',
        help='Archivo de configuracion JSON'
    )
    parser.add_argument(
        '--cert',
        metavar='FILE',
        help='Archivo de certificado .pfx'
    )
    parser.add_argument(
        '--cert-password',
        metavar='PASSWORD',
        help='Contrasena del certificado'
    )
    parser.add_argument(
        '--output',
        metavar='DIR',
        default='./output',
        help='Directorio de salida (default: ./output)'
    )
    parser.add_argument(
        '--no-send',
        action='store_true',
        help='Solo generar XML, no enviar a DIAN'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='dian_fe 1.0.0'
    )

    args = parser.parse_args()

    if args.status:
        return cmd_status(args)

    if args.verificar:
        return cmd_verificar(args)

    if args.lote:
        return cmd_lote(args)

    if args.tipo:
        return cmd_documento(args)

    parser.print_help()
    return 1


def load_config(args) -> dict:
    """Cargar configuracion desde archivo o argumentos."""
    config = {}

    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    if args.cert:
        config['certificate_path'] = args.cert
    if args.cert_password:
        config['certificate_password'] = args.cert_password

    return config


def cmd_status(args) -> int:
    """Consultar estado por ZipKey."""
    from .dian_client import DianClient

    config = load_config(args)

    client = DianClient(
        certificate_path=config.get('certificate_path'),
        certificate_password=config.get('certificate_password'),
        environment=config.get('environment', 'habilitacion')
    )

    response = client.get_status_zip(args.status)

    print(f"ZipKey: {args.status}")
    print(f"IsValid: {response.is_valid}")
    print(f"StatusCode: {response.status_code}")
    print(f"StatusDescription: {response.status_description}")

    if response.error_messages:
        print(f"Errores: {response.error_messages}")

    return 0 if response.is_valid else 1


def cmd_verificar(args) -> int:
    """Verificar documentos pendientes."""
    from .tracker import DocumentTracker

    tracker = DocumentTracker()
    summary = tracker.get_summary()

    print("Resumen de documentos:")
    print(f"  Facturas: {summary['facturas']}")
    print(f"  Notas Credito: {summary['notas_credito']}")
    print(f"  Notas Debito: {summary['notas_debito']}")
    print(f"  Ultimo consecutivo: {summary['last_consecutive']}")

    return 0


def cmd_lote(args) -> int:
    """Enviar lote de habilitacion."""
    print("Funcion de lote no implementada en CLI basico.")
    print("Use la API de Python directamente para lotes.")
    return 1


def cmd_documento(args) -> int:
    """Generar y enviar documento individual."""
    print(f"Generando documento tipo: {args.tipo}")
    print("Use la API de Python directamente para generar documentos.")
    return 1


def create_zip(xml_content: bytes, file_name: str) -> bytes:
    """
    Crear archivo ZIP con documento XML.

    Args:
        xml_content: Contenido XML en bytes
        file_name: Nombre del archivo XML

    Returns:
        Contenido del ZIP en bytes
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(file_name, xml_content)
    return zip_buffer.getvalue()


if __name__ == '__main__':
    sys.exit(main())
