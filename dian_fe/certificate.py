# This file is part of dian_fe.
"""
Manejo de certificados PKCS#12 para firma digital DIAN.
"""

import base64
import hashlib
from typing import Tuple, List, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


def load_certificate(pfx_path: str, password: str) -> Tuple:
    """
    Cargar certificado PKCS#12.

    Args:
        pfx_path: Ruta al archivo .pfx o .p12
        password: Contrasena del certificado

    Returns:
        Tupla (private_key, certificate, chain)
    """
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()

    return load_certificate_from_bytes(pfx_data, password)


def load_certificate_from_bytes(pfx_data: bytes, password: str) -> Tuple:
    """
    Cargar certificado PKCS#12 desde bytes.

    Args:
        pfx_data: Datos del archivo .pfx o .p12
        password: Contrasena del certificado

    Returns:
        Tupla (private_key, certificate, chain)
    """
    private_key, certificate, chain = pkcs12.load_key_and_certificates(
        pfx_data, password.encode(), default_backend()
    )

    return private_key, certificate, list(chain) if chain else []


def cert_to_base64(cert) -> str:
    """
    Convertir certificado a base64 (formato DER).

    Args:
        cert: Certificado X.509

    Returns:
        Certificado en base64
    """
    der = cert.public_bytes(serialization.Encoding.DER)
    return base64.b64encode(der).decode('utf-8')


def cert_digest(cert) -> str:
    """
    Calcular digest SHA-256 del certificado en base64.

    Args:
        cert: Certificado X.509

    Returns:
        Digest en base64
    """
    der = cert.public_bytes(serialization.Encoding.DER)
    return base64.b64encode(hashlib.sha256(der).digest()).decode('utf-8')


def get_issuer_dn(cert) -> str:
    """
    Obtener IssuerDN en formato RFC2253.

    NOTA: Se usa el orden natural del certificado, sin invertir.
    Esto es compatible con la implementacion PHP de Stenfrank/ubl21dian.

    Args:
        cert: Certificado X.509

    Returns:
        IssuerDN formateado
    """
    parts = []
    name_map = {
        'commonName': 'CN',
        'organizationalUnitName': 'OU',
        'organizationName': 'O',
        'localityName': 'L',
        'stateOrProvinceName': 'ST',
        'countryName': 'C',
        'emailAddress': 'emailAddress',
        'serialNumber': 'serialNumber',
    }

    for attr in cert.issuer:
        oid_name = attr.oid._name
        name = name_map.get(oid_name, oid_name)
        parts.append(f"{name}={attr.value}")

    # NO invertir - usar orden natural como hace PHP
    return ','.join(parts)


def get_subject_dn(cert) -> str:
    """
    Obtener SubjectDN en formato RFC2253.

    Args:
        cert: Certificado X.509

    Returns:
        SubjectDN formateado
    """
    parts = []
    name_map = {
        'commonName': 'CN',
        'organizationalUnitName': 'OU',
        'organizationName': 'O',
        'localityName': 'L',
        'stateOrProvinceName': 'ST',
        'countryName': 'C',
        'emailAddress': 'emailAddress',
        'serialNumber': 'serialNumber',
    }

    for attr in cert.subject:
        oid_name = attr.oid._name
        name = name_map.get(oid_name, oid_name)
        parts.append(f"{name}={attr.value}")

    return ','.join(parts)


def sign_data(private_key, data: bytes) -> str:
    """
    Firmar datos con RSA-SHA256 y retornar en base64.

    Args:
        private_key: Clave privada
        data: Datos a firmar

    Returns:
        Firma en base64
    """
    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')
