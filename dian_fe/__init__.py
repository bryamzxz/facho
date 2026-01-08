# This file is part of dian_fe.
"""
DIAN Facturacion Electronica - Libreria Python

Libreria modular para facturacion electronica DIAN Colombia.
Soporta: Facturas, Notas Credito, Notas Debito.
Compatible con Anexo Tecnico DIAN v1.9.

Ejemplo de uso:
    from dian_fe import XAdESSigner, InvoiceBuilder, DianClient, InvoiceConfig, Party, Address, InvoiceLine

    # Configurar
    config = InvoiceConfig(
        software_id='...',
        software_pin='...',
        technical_key='...',
        nit='1001186599',
        company_name='Mi Empresa',
        resolution_number='18760000001',
        resolution_date='2019-01-19',
        resolution_end_date='2030-01-19',
        prefix='SETP',
        range_from='990000000',
        range_to='995000000',
        environment='2'
    )

    # Crear factura
    builder = InvoiceBuilder(config)
    xml = builder.build(
        number='SETP990000001',
        issue_date='2026-01-08',
        issue_time='10:30:00-05:00',
        supplier=supplier,
        customer=customer,
        lines=[InvoiceLine(...)]
    )

    # Firmar
    signer = XAdESSigner.from_pkcs12('certificado.pfx', 'password')
    signed_xml = signer.sign(xml)

    # Enviar a DIAN
    client = DianClient.from_pkcs12('certificado.pfx', 'password')
    response = client.send_test_set_async('fv001.zip', zip_content, test_set_id)
"""

__version__ = '1.0.0'
__author__ = 'DIAN FE Team'

# Configuracion y constantes
from .config import (
    CONFIG,
    NS,
    NS_SOAP,
    DOC_TYPES,
    CREDIT_REASONS,
    DEBIT_REASONS,
    TAX_CODES,
    ENDPOINT_HABILITACION,
    ENDPOINT_PRODUCCION,
    set_config,
    get_config,
)

# Utilidades
from .utils import (
    calcular_dv,
    calcular_cufe,
    calcular_cude,
    calcular_software_security_code,
    sha256_digest,
    sha384_digest,
)

# Certificados
from .certificate import (
    load_certificate,
    load_certificate_from_bytes,
    cert_to_base64,
    cert_digest,
    get_issuer_dn,
    get_subject_dn,
    sign_data,
)

# Firma XAdES-EPES
from .xades_signer import XAdESSigner

# Constructores XML
from .xml_builder import (
    InvoiceBuilder,
    CreditNoteBuilder,
    DebitNoteBuilder,
    InvoiceConfig,
    Party,
    Address,
    InvoiceLine,
)

# Cliente DIAN
from .dian_client import DianClient, DianResponse

# Tracker
from .tracker import DocumentTracker

__all__ = [
    # Version
    '__version__',

    # Configuracion
    'CONFIG',
    'NS',
    'NS_SOAP',
    'DOC_TYPES',
    'CREDIT_REASONS',
    'DEBIT_REASONS',
    'TAX_CODES',
    'ENDPOINT_HABILITACION',
    'ENDPOINT_PRODUCCION',
    'set_config',
    'get_config',

    # Utilidades
    'calcular_dv',
    'calcular_cufe',
    'calcular_cude',
    'calcular_software_security_code',
    'sha256_digest',
    'sha384_digest',

    # Certificados
    'load_certificate',
    'load_certificate_from_bytes',
    'cert_to_base64',
    'cert_digest',
    'get_issuer_dn',
    'get_subject_dn',
    'sign_data',

    # Firma
    'XAdESSigner',

    # Builders
    'InvoiceBuilder',
    'CreditNoteBuilder',
    'DebitNoteBuilder',
    'InvoiceConfig',
    'Party',
    'Address',
    'InvoiceLine',

    # Cliente
    'DianClient',
    'DianResponse',

    # Tracker
    'DocumentTracker',
]
