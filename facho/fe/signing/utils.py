# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Utilidades para firma digital.
"""

import base64
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


def sha256_digest(data: bytes) -> str:
    """Calcular digest SHA256 y retornar en base64."""
    return base64.b64encode(hashlib.sha256(data).digest()).decode('utf-8')


def sha384_digest(data: bytes) -> str:
    """Calcular digest SHA384 y retornar en hexadecimal."""
    return hashlib.sha384(data).hexdigest()


def sign_data(private_key, data: bytes) -> str:
    """Firmar datos con RSA-SHA256 y retornar en base64."""
    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')


def verify_signature(public_key, signature: bytes, data: bytes) -> bool:
    """Verificar firma RSA-SHA256."""
    try:
        public_key.verify(
            signature,
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
