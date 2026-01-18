# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Utilidades para construir mensajes SOAP con WS-Security para DIAN.

IMPORTANTE:
- Documento UBL usa C14N INCLUSIVO (exclusive=False)
- SOAP WS-Security usa C14N EXCLUSIVO (exclusive=True con inclusive_ns_prefixes)

Este modulo proporciona funciones para construir el envelope SOAP
firmado con WS-Security para comunicacion con los servicios web DIAN.
"""

import uuid
import base64
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from lxml import etree

from .constants import NS_SOAP, C14N_EXC_ALG, RSA_SHA256, SHA256_ALG, DIAN_ENDPOINTS


def sha256_digest_b64(data: bytes) -> str:
    """
    Calcular digest SHA256 y codificar en base64.

    Args:
        data: Bytes a hashear

    Returns:
        Hash SHA256 codificado en base64
    """
    return base64.b64encode(hashlib.sha256(data).digest()).decode('utf-8')


def sign_data_rsa_sha256(private_key, data: bytes) -> str:
    """
    Firmar datos con RSA-SHA256.

    Args:
        private_key: Clave privada RSA
        data: Bytes a firmar

    Returns:
        Firma codificada en base64
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('ascii')


def generate_wssec_ids(suffix: str = None) -> dict:
    """
    Generar IDs unicos para elementos WS-Security.

    Args:
        suffix: Sufijo opcional (default: UUID aleatorio)

    Returns:
        Diccionario con los IDs generados
    """
    if suffix is None:
        suffix = uuid.uuid4().hex[:8]

    return {
        'timestamp': f'TS-{suffix}',
        'token': f'X509-{suffix}',
        'signature': f'SIG-{suffix}',
        'keyinfo': f'KI-{suffix}',
        'str': f'STR-{suffix}',
        'to': f'id-TO-{suffix}',
    }


def generate_timestamps(validity_hours: int = 5) -> Tuple[str, str]:
    """
    Generar timestamps para WS-Security.

    Args:
        validity_hours: Horas de validez del mensaje

    Returns:
        Tuple (created, expires) en formato ISO
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=validity_hours)

    created_str = now.strftime('%Y-%m-%dT%H:%M:%S.') + f'{now.microsecond // 1000:03d}Z'
    expires_str = exp.strftime('%Y-%m-%dT%H:%M:%S.') + f'{exp.microsecond // 1000:03d}Z'

    return created_str, expires_str


def build_soap_envelope_template(
    body_content: str,
    action: str,
    endpoint: str,
    cert_b64: str,
    ids: dict,
    created: str,
    expires: str
) -> str:
    """
    Construir plantilla de envelope SOAP con WS-Security.

    Args:
        body_content: Contenido XML del body SOAP
        action: Accion SOAP (URL)
        endpoint: Endpoint del servicio
        cert_b64: Certificado en base64
        ids: Diccionario con IDs de elementos
        created: Timestamp de creacion
        expires: Timestamp de expiracion

    Returns:
        Plantilla XML del envelope SOAP
    """
    return f'''<soap:Envelope xmlns:soap="{NS_SOAP['soap']}" xmlns:wcf="{NS_SOAP['wcf']}">
<soap:Header xmlns:wsa="{NS_SOAP['wsa']}">
<wsse:Security xmlns:wsse="{NS_SOAP['wsse']}" xmlns:wsu="{NS_SOAP['wsu']}">
<wsu:Timestamp wsu:Id="{ids['timestamp']}">
<wsu:Created>{created}</wsu:Created>
<wsu:Expires>{expires}</wsu:Expires>
</wsu:Timestamp>
<wsse:BinarySecurityToken EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary" ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3" wsu:Id="{ids['token']}">{cert_b64}</wsse:BinarySecurityToken>
<ds:Signature xmlns:ds="{NS_SOAP['ds']}" Id="{ids['signature']}">
<ds:KeyInfo Id="{ids['keyinfo']}">
<wsse:SecurityTokenReference wsu:Id="{ids['str']}">
<wsse:Reference URI="#{ids['token']}" ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3"/>
</wsse:SecurityTokenReference>
</ds:KeyInfo>
</ds:Signature>
</wsse:Security>
<wsa:Action>{action}</wsa:Action>
<wsa:To xmlns:wsu="{NS_SOAP['wsu']}" wsu:Id="{ids['to']}">{endpoint}</wsa:To>
</soap:Header>
<soap:Body>{body_content}</soap:Body>
</soap:Envelope>'''


def build_signed_info_xml(
    ids: dict,
    ts_digest: str,
    to_digest: str
) -> str:
    """
    Construir SignedInfo XML para firma SOAP WS-Security.

    CRITICO: Usa C14N EXCLUSIVO con inclusive_ns_prefixes.

    Args:
        ids: Diccionario con IDs de elementos
        ts_digest: Digest del Timestamp
        to_digest: Digest del elemento To

    Returns:
        XML de SignedInfo
    """
    return f'''<ds:SignedInfo xmlns:ds="{NS_SOAP['ds']}" xmlns:soap="{NS_SOAP['soap']}" xmlns:wsa="{NS_SOAP['wsa']}" xmlns:wsu="{NS_SOAP['wsu']}">
<ds:CanonicalizationMethod Algorithm="{C14N_EXC_ALG}">
<ec:InclusiveNamespaces xmlns:ec="{NS_SOAP['ec']}" PrefixList="soap wsa"/>
</ds:CanonicalizationMethod>
<ds:SignatureMethod Algorithm="{RSA_SHA256}"/>
<ds:Reference URI="#{ids['timestamp']}">
<ds:Transforms>
<ds:Transform Algorithm="{C14N_EXC_ALG}">
<ec:InclusiveNamespaces xmlns:ec="{NS_SOAP['ec']}" PrefixList="wsu soap"/>
</ds:Transform>
</ds:Transforms>
<ds:DigestMethod Algorithm="{SHA256_ALG}"/>
<ds:DigestValue>{ts_digest}</ds:DigestValue>
</ds:Reference>
<ds:Reference URI="#{ids['to']}">
<ds:Transforms>
<ds:Transform Algorithm="{C14N_EXC_ALG}">
<ec:InclusiveNamespaces xmlns:ec="{NS_SOAP['ec']}" PrefixList="wsu soap wsa"/>
</ds:Transform>
</ds:Transforms>
<ds:DigestMethod Algorithm="{SHA256_ALG}"/>
<ds:DigestValue>{to_digest}</ds:DigestValue>
</ds:Reference>
</ds:SignedInfo>'''


def build_wssec_soap(
    body_content: str,
    action: str,
    endpoint: str,
    private_key,
    cert_b64: str,
    validity_hours: int = 5
) -> str:
    """
    Construir mensaje SOAP completo con WS-Security firmado.

    CRITICO:
    - Usa C14N EXCLUSIVO (exclusive=True) con inclusive_ns_prefixes para SOAP
    - Este es diferente a documentos UBL que usan C14N INCLUSIVO

    Args:
        body_content: Contenido XML del body SOAP
        action: Accion SOAP (URL completa)
        endpoint: Endpoint del servicio DIAN
        private_key: Clave privada para firmar
        cert_b64: Certificado X.509 en base64
        validity_hours: Horas de validez del mensaje

    Returns:
        Mensaje SOAP firmado como string XML
    """
    # Generar IDs y timestamps
    ids = generate_wssec_ids()
    created, expires = generate_timestamps(validity_hours)

    # Crear plantilla del envelope
    soap_template = build_soap_envelope_template(
        body_content, action, endpoint, cert_b64, ids, created, expires
    )

    # Parsear para calcular digests
    doc = etree.fromstring(soap_template.encode('utf-8'))

    # Encontrar elementos a firmar
    timestamp = doc.find('.//{%s}Timestamp' % NS_SOAP['wsu'])
    to_el = doc.find('.//{%s}To' % NS_SOAP['wsa'])

    # Calcular digests con C14N EXCLUSIVO
    # IMPORTANTE: inclusive_ns_prefixes mantiene namespaces requeridos
    ts_c14n = etree.tostring(
        timestamp, method='c14n', exclusive=True, with_comments=False,
        inclusive_ns_prefixes=['wsu', 'soap']
    )
    ts_digest = sha256_digest_b64(ts_c14n)

    to_c14n = etree.tostring(
        to_el, method='c14n', exclusive=True, with_comments=False,
        inclusive_ns_prefixes=['wsu', 'soap', 'wsa']
    )
    to_digest = sha256_digest_b64(to_c14n)

    # Obtener elemento Signature
    sig = doc.find('.//{%s}Signature' % NS_SOAP['ds'])

    # Construir SignedInfo
    signed_info_xml = build_signed_info_xml(ids, ts_digest, to_digest)
    si_doc = etree.fromstring(signed_info_xml.encode('utf-8'))

    # Canonicalizar SignedInfo para firma
    si_c14n = etree.tostring(
        si_doc, method='c14n', exclusive=True, with_comments=False,
        inclusive_ns_prefixes=['soap', 'wsa']
    )

    # Firmar
    sig_value = sign_data_rsa_sha256(private_key, si_c14n)

    # Crear elemento SignatureValue
    sig_val_el = etree.Element('{%s}SignatureValue' % NS_SOAP['ds'])
    sig_val_el.text = sig_value

    # Obtener KeyInfo existente
    key_info = sig.find('.//{%s}KeyInfo' % NS_SOAP['ds'])

    # Reconstruir Signature con elementos en orden correcto
    sig.remove(key_info)

    # Insertar: SignedInfo, SignatureValue, KeyInfo
    sig.insert(0, si_doc)
    sig.insert(1, sig_val_el)
    sig.append(key_info)

    return etree.tostring(doc, encoding='unicode')


def get_endpoint(environment: str) -> str:
    """
    Obtener endpoint DIAN segun ambiente.

    Args:
        environment: 'produccion' o 'habilitacion'

    Returns:
        URL del endpoint
    """
    if environment.lower() in ('produccion', 'production', '1'):
        return DIAN_ENDPOINTS['produccion']
    return DIAN_ENDPOINTS['habilitacion']


# =============================================================================
# ACCIONES SOAP DIAN
# =============================================================================

SOAP_ACTIONS = {
    'SendTestSetAsync': 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendTestSetAsync',
    'SendBillSync': 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendBillSync',
    'SendBillAsync': 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendBillAsync',
    'GetStatus': 'http://wcf.dian.colombia/IWcfDianCustomerServices/GetStatus',
    'GetStatusZip': 'http://wcf.dian.colombia/IWcfDianCustomerServices/GetStatusZip',
    'GetNumberingRange': 'http://wcf.dian.colombia/IWcfDianCustomerServices/GetNumberingRange',
}


def build_send_test_set_body(file_name: str, content_b64: str, test_set_id: str) -> str:
    """
    Construir body para SendTestSetAsync.

    Args:
        file_name: Nombre del archivo ZIP
        content_b64: Contenido del ZIP en base64
        test_set_id: ID del set de pruebas

    Returns:
        XML del body SOAP
    """
    return f'''<wcf:SendTestSetAsync xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:fileName>{file_name}</wcf:fileName>
<wcf:contentFile>{content_b64}</wcf:contentFile>
<wcf:testSetId>{test_set_id}</wcf:testSetId>
</wcf:SendTestSetAsync>'''


def build_send_bill_sync_body(file_name: str, content_b64: str) -> str:
    """
    Construir body para SendBillSync.

    Args:
        file_name: Nombre del archivo ZIP
        content_b64: Contenido del ZIP en base64

    Returns:
        XML del body SOAP
    """
    return f'''<wcf:SendBillSync xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:fileName>{file_name}</wcf:fileName>
<wcf:contentFile>{content_b64}</wcf:contentFile>
</wcf:SendBillSync>'''


def build_send_bill_async_body(file_name: str, content_b64: str) -> str:
    """
    Construir body para SendBillAsync.

    Args:
        file_name: Nombre del archivo ZIP
        content_b64: Contenido del ZIP en base64

    Returns:
        XML del body SOAP
    """
    return f'''<wcf:SendBillAsync xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:fileName>{file_name}</wcf:fileName>
<wcf:contentFile>{content_b64}</wcf:contentFile>
</wcf:SendBillAsync>'''


def build_get_status_body(track_id: str) -> str:
    """
    Construir body para GetStatus.

    Args:
        track_id: TrackId del documento (CUFE/CUDE)

    Returns:
        XML del body SOAP
    """
    return f'''<wcf:GetStatus xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:trackId>{track_id}</wcf:trackId>
</wcf:GetStatus>'''


def build_get_status_zip_body(track_id: str) -> str:
    """
    Construir body para GetStatusZip.

    Args:
        track_id: TrackId o ZipKey del documento

    Returns:
        XML del body SOAP
    """
    return f'''<wcf:GetStatusZip xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:trackId>{track_id}</wcf:trackId>
</wcf:GetStatusZip>'''


def build_get_numbering_range_body(account_code: str, software_code: str) -> str:
    """
    Construir body para GetNumberingRange.

    Args:
        account_code: Codigo de cuenta (NIT)
        software_code: Codigo del software

    Returns:
        XML del body SOAP
    """
    return f'''<wcf:GetNumberingRange xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:accountCode>{account_code}</wcf:accountCode>
<wcf:softwareCode>{software_code}</wcf:softwareCode>
</wcf:GetNumberingRange>'''
