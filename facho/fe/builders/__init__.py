# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constructores de documentos XML UBL 2.1 para DIAN Colombia.
"""

# Builders principales
from .invoice_builder import (
    InvoiceBuilder,
    InvoiceConfig,
    InvoiceData,
    InvoiceLine,
    Party,
    Address,
)
from .credit_note_builder import CreditNoteBuilder, CreditNoteData
from .debit_note_builder import DebitNoteBuilder, DebitNoteData, DEBIT_REASONS

# Builders adicionales
from .support_document_builder import SupportDocumentBuilder, SupportDocumentData
from .export_invoice_builder import (
    ExportInvoiceBuilder,
    ExportInvoiceData,
    DeliveryTerms,
    DeliveryInfo,
    ExchangeRate,
)
from .contingency_invoice_builder import (
    ContingencyInvoiceBuilder,
    ContingencyInvoiceData,
)

# AllowanceCharge (descuentos y cargos)
from .allowance_charge import (
    AllowanceCharge,
    add_allowance_charges_to_element,
    calculate_totals,
    create_discount,
    create_charge,
    ALLOWANCE_REASON_CODES,
    CHARGE_REASON_CODES,
)

# Sistema de impuestos
from .taxes import (
    Tax,
    TaxTotal,
    TAX_CODES as TAX_CODES_FULL,
    TAX_NAMES,
    WITHHOLDING_TAX_CODES,
    IVA_RATES,
    RETENTION_RATES,
    truncar,
    truncar_decimal,
    formato_dinero,
    agrupar_impuestos,
    separar_impuestos_retenciones,
    calcular_totales_impuestos,
)

# Sistema de excepciones
from .exceptions import (
    FachoError,
    ValidationError,
    ConfigurationError,
    SignatureError,
    CertificateError,
    DianError,
    XmlBuildError,
    CufeError,
    RangeError,
    NetworkError,
    FachoTimeoutError,
    DIAN_ERROR_CODES,
    get_dian_error_description,
    parse_dian_errors,
)

# Validadores
from .validators import (
    InvoiceValidator,
    ConfigValidator,
    PartyValidator,
    InvoiceLineValidator,
    validate_invoice,
    validate_before_build,
    validate_nit,
    validate_date,
    validate_time,
    validate_uuid,
    validate_not_empty,
    validate_positive_number,
)

# Constantes
from .constants import (
    NS,
    SCHEME_AGENCY_ATTRS,
    DIAN_PROFILE_ID,
    DIAN_PROFILE_ID_CREDIT_NOTE,
    DIAN_PROFILE_ID_DEBIT_NOTE,
    DIAN_PROFILE_ID_EXPORT,
    DIAN_PROFILE_ID_CONTINGENCY,
    DIAN_PROFILE_ID_SUPPORT,
    DIAN_UBL_VERSION,
    DIAN_CUSTOMIZATION_ID,
    INVOICE_TYPE_CODE,
    CREDIT_NOTE_TYPE_CODE,
    DEBIT_NOTE_TYPE_CODE,
    EXPORT_INVOICE_TYPE_CODE,
    CONTINGENCY_INVOICE_TYPE_CODE,
    SUPPORT_DOCUMENT_TYPE_CODE,
    TAX_CODES,
    CREDIT_REASONS,
    DOC_TYPES,
    COUNTRY_ID_ATTRS,
    AUTHORIZATION_PROVIDER_ID,
    INCOTERMS,
    CURRENCIES,
)

__all__ = [
    # Builders
    'InvoiceBuilder',
    'CreditNoteBuilder',
    'DebitNoteBuilder',
    'SupportDocumentBuilder',
    'ExportInvoiceBuilder',
    'ContingencyInvoiceBuilder',
    # Data classes
    'InvoiceConfig',
    'InvoiceData',
    'InvoiceLine',
    'Party',
    'Address',
    'CreditNoteData',
    'DebitNoteData',
    'SupportDocumentData',
    'ExportInvoiceData',
    'ContingencyInvoiceData',
    'DeliveryTerms',
    'DeliveryInfo',
    'ExchangeRate',
    'AllowanceCharge',
    # Tax classes and functions
    'Tax',
    'TaxTotal',
    'truncar',
    'truncar_decimal',
    'formato_dinero',
    'agrupar_impuestos',
    'separar_impuestos_retenciones',
    'calcular_totales_impuestos',
    # AllowanceCharge functions
    'add_allowance_charges_to_element',
    'calculate_totals',
    'create_discount',
    'create_charge',
    # Exceptions
    'FachoError',
    'ValidationError',
    'ConfigurationError',
    'SignatureError',
    'CertificateError',
    'DianError',
    'XmlBuildError',
    'CufeError',
    'RangeError',
    'NetworkError',
    'FachoTimeoutError',
    'DIAN_ERROR_CODES',
    'get_dian_error_description',
    'parse_dian_errors',
    # Validators
    'InvoiceValidator',
    'ConfigValidator',
    'PartyValidator',
    'InvoiceLineValidator',
    'validate_invoice',
    'validate_before_build',
    'validate_nit',
    'validate_date',
    'validate_time',
    'validate_uuid',
    'validate_not_empty',
    'validate_positive_number',
    # Constants
    'NS',
    'SCHEME_AGENCY_ATTRS',
    'DIAN_PROFILE_ID',
    'DIAN_PROFILE_ID_CREDIT_NOTE',
    'DIAN_PROFILE_ID_DEBIT_NOTE',
    'DIAN_PROFILE_ID_EXPORT',
    'DIAN_PROFILE_ID_CONTINGENCY',
    'DIAN_PROFILE_ID_SUPPORT',
    'DIAN_UBL_VERSION',
    'DIAN_CUSTOMIZATION_ID',
    'INVOICE_TYPE_CODE',
    'CREDIT_NOTE_TYPE_CODE',
    'DEBIT_NOTE_TYPE_CODE',
    'EXPORT_INVOICE_TYPE_CODE',
    'CONTINGENCY_INVOICE_TYPE_CODE',
    'SUPPORT_DOCUMENT_TYPE_CODE',
    'TAX_CODES',
    'TAX_CODES_FULL',
    'TAX_NAMES',
    'WITHHOLDING_TAX_CODES',
    'IVA_RATES',
    'RETENTION_RATES',
    'CREDIT_REASONS',
    'DEBIT_REASONS',
    'DOC_TYPES',
    'COUNTRY_ID_ATTRS',
    'AUTHORIZATION_PROVIDER_ID',
    'INCOTERMS',
    'CURRENCIES',
    'ALLOWANCE_REASON_CODES',
    'CHARGE_REASON_CODES',
]
