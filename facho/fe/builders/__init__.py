# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constructores de documentos XML UBL 2.1 para DIAN Colombia.
"""

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
from .constants import (
    NS,
    SCHEME_AGENCY_ATTRS,
    DIAN_PROFILE_ID,
    DIAN_PROFILE_ID_CREDIT_NOTE,
    DIAN_PROFILE_ID_DEBIT_NOTE,
    DIAN_UBL_VERSION,
    DIAN_CUSTOMIZATION_ID,
    INVOICE_TYPE_CODE,
    CREDIT_NOTE_TYPE_CODE,
    DEBIT_NOTE_TYPE_CODE,
    TAX_CODES,
    CREDIT_REASONS,
    DOC_TYPES,
)

__all__ = [
    # Builders
    'InvoiceBuilder',
    'CreditNoteBuilder',
    'DebitNoteBuilder',
    # Data classes
    'InvoiceConfig',
    'InvoiceData',
    'InvoiceLine',
    'Party',
    'Address',
    'CreditNoteData',
    'DebitNoteData',
    # Constants
    'NS',
    'SCHEME_AGENCY_ATTRS',
    'DIAN_PROFILE_ID',
    'DIAN_PROFILE_ID_CREDIT_NOTE',
    'DIAN_PROFILE_ID_DEBIT_NOTE',
    'DIAN_UBL_VERSION',
    'DIAN_CUSTOMIZATION_ID',
    'INVOICE_TYPE_CODE',
    'CREDIT_NOTE_TYPE_CODE',
    'DEBIT_NOTE_TYPE_CODE',
    'TAX_CODES',
    'CREDIT_REASONS',
    'DEBIT_REASONS',
    'DOC_TYPES',
]
