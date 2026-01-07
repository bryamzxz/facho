# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Modulo de firma XAdES-EPES para DIAN Colombia.
Implementacion pura sin dependencias de xmlsig/xades.
Basado en implementacion funcional aprobada por DIAN.
"""

from .xades import XAdESSigner, sign_invoice_xades
from .certificate import load_certificate, cert_to_base64, cert_digest, get_issuer_dn
from .utils import sha256_digest, sign_data

__all__ = [
    'XAdESSigner',
    'sign_invoice_xades',
    'load_certificate',
    'cert_to_base64',
    'cert_digest',
    'get_issuer_dn',
    'sha256_digest',
    'sign_data',
]
