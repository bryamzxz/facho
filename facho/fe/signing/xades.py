# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Firma XAdES-EPES para DIAN Colombia.
Implementacion pura basada en script funcional aprobado por DIAN.
"""

import uuid
import base64
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from lxml import etree
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from .certificate import cert_to_base64, cert_digest, get_issuer_dn
from .utils import sha256_digest


# =============================================================================
# CONSTANTES
# =============================================================================

# Namespaces para firma
NS = {
    'fe': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xades': 'http://uri.etsi.org/01903/v1.3.2#',
    'xades141': 'http://uri.etsi.org/01903/v1.4.1#',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
}

# Algoritmos
C14N_ALG = 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
C14N_EXC_ALG = 'http://www.w3.org/2001/10/xml-exc-c14n#'
ENVELOPED_SIG = 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
RSA_SHA256 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
SHA256_ALG = 'http://www.w3.org/2001/04/xmlenc#sha256'
SIGNED_PROPS_TYPE = 'http://uri.etsi.org/01903#SignedProperties'

# Politica de firma DIAN v2
POLITICA_URL = 'https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf'
POLITICA_HASH = 'dMoMvtcG5aIzgYo0tIsSQeVJBDnUnfSOfBpxXrmor0Y='
POLITICA_NAME = 'Politica de firma para facturas electronicas de la Republica de Colombia.'


class XAdESSigner:
    """
    Firmador XAdES-EPES para documentos DIAN.

    Implementa la firma digital segun especificaciones DIAN usando
    el algoritmo RSA-SHA256 y politica de firma v2.
    """

    def __init__(self, private_key, certificate, chain: Optional[List] = None):
        """
        Inicializar firmador.

        Args:
            private_key: Clave privada del certificado
            certificate: Certificado X.509
            chain: Lista opcional de certificados intermedios
        """
        self.private_key = private_key
        self.certificate = certificate
        self.chain = chain or []

    @classmethod
    def from_pkcs12(cls, pfx_path: str, password: str) -> 'XAdESSigner':
        """
        Crear firmador desde archivo PKCS#12.

        Args:
            pfx_path: Ruta al archivo .pfx o .p12
            password: Contrasena del certificado

        Returns:
            Instancia de XAdESSigner
        """
        from .certificate import load_certificate
        private_key, certificate, chain = load_certificate(pfx_path, password)
        return cls(private_key, certificate, chain)

    @classmethod
    def from_pkcs12_bytes(cls, pfx_data: bytes, password: str) -> 'XAdESSigner':
        """
        Crear firmador desde bytes PKCS#12.

        Args:
            pfx_data: Datos del archivo .pfx o .p12
            password: Contrasena del certificado

        Returns:
            Instancia de XAdESSigner
        """
        from .certificate import load_certificate_from_bytes
        private_key, certificate, chain = load_certificate_from_bytes(pfx_data, password)
        return cls(private_key, certificate, chain)

    def sign(self, xml_element: etree._Element, ext_ns: str = None) -> etree._Element:
        """
        Firmar documento XML con XAdES-EPES.

        Args:
            xml_element: Elemento XML a firmar
            ext_ns: Namespace de ExtensionContent (default: UBL CommonExtensionComponents)

        Returns:
            Elemento XML firmado
        """
        ext_ns = ext_ns or NS['ext']
        return sign_invoice_xades(
            xml_element,
            self.private_key,
            self.certificate,
            self.chain,
            ext_ns
        )

    def verify(self, signed_element: etree._Element) -> bool:
        """
        Verificar firma de documento XML.

        Args:
            signed_element: Elemento XML firmado

        Returns:
            True si la firma es valida
        """
        # TODO: Implementar verificacion completa
        return True


def sign_invoice_xades(
    invoice: etree._Element,
    private_key,
    cert,
    chain: list,
    ext_ns: str = None
) -> etree._Element:
    """
    Firmar factura con XAdES-EPES.

    METODO: Insertar estructura primero, luego extraer y calcular digests.
    Este metodo es compatible con la validacion DIAN.

    Args:
        invoice: Elemento XML de la factura
        private_key: Clave privada
        cert: Certificado X.509
        chain: Lista de certificados intermedios
        ext_ns: Namespace de ExtensionContent

    Returns:
        Elemento XML firmado
    """
    ext_ns = ext_ns or NS['ext']

    # IDs unicos
    sig_id = f"xmldsig-{uuid.uuid4().hex[:12]}"
    signed_props_id = f"xmldsig-{uuid.uuid4().hex[:12]}-signedprops"
    keyinfo_id = f"xmldsig-{uuid.uuid4().hex[:12]}-keyinfo"
    ref_id = f"xmldsig-{uuid.uuid4().hex[:12]}-ref0"

    cert_b64 = cert_to_base64(cert)
    signing_time = datetime.now(timezone(timedelta(hours=-5))).strftime('%Y-%m-%dT%H:%M:%S-05:00')

    # =========================================================================
    # PASO 1: CALCULAR DIGEST DEL DOCUMENTO (antes de insertar firma)
    # =========================================================================
    doc_c14n = etree.tostring(invoice, method='c14n', exclusive=False, with_comments=False)
    doc_digest = sha256_digest(doc_c14n)

    # =========================================================================
    # PASO 2: INSERTAR ESTRUCTURA DE FIRMA EN EL DOCUMENTO
    # =========================================================================
    ext_contents = invoice.findall('.//{%s}ExtensionContent' % ext_ns)
    if len(ext_contents) < 2:
        raise ValueError("El documento debe tener al menos 2 UBLExtension/ExtensionContent")

    sig_container = ext_contents[1]

    # Crear Signature
    signature = etree.SubElement(
        sig_container,
        '{%s}Signature' % NS['ds'],
        nsmap={'ds': NS['ds']}
    )
    signature.set('Id', sig_id)

    # SignedInfo con placeholders para DigestValue
    si = etree.SubElement(signature, '{%s}SignedInfo' % NS['ds'])
    etree.SubElement(si, '{%s}CanonicalizationMethod' % NS['ds']).set('Algorithm', C14N_ALG)
    etree.SubElement(si, '{%s}SignatureMethod' % NS['ds']).set('Algorithm', RSA_SHA256)

    # Reference 1: documento
    ref1 = etree.SubElement(si, '{%s}Reference' % NS['ds'])
    ref1.set('Id', ref_id)
    ref1.set('URI', '')
    tr = etree.SubElement(ref1, '{%s}Transforms' % NS['ds'])
    etree.SubElement(tr, '{%s}Transform' % NS['ds']).set('Algorithm', ENVELOPED_SIG)
    etree.SubElement(ref1, '{%s}DigestMethod' % NS['ds']).set('Algorithm', SHA256_ALG)
    ref1_dv = etree.SubElement(ref1, '{%s}DigestValue' % NS['ds'])
    ref1_dv.text = doc_digest

    # Reference 2: KeyInfo (placeholder)
    ref2 = etree.SubElement(si, '{%s}Reference' % NS['ds'])
    ref2.set('URI', f'#{keyinfo_id}')
    etree.SubElement(ref2, '{%s}DigestMethod' % NS['ds']).set('Algorithm', SHA256_ALG)
    ref2_dv = etree.SubElement(ref2, '{%s}DigestValue' % NS['ds'])
    ref2_dv.text = 'PLACEHOLDER'

    # Reference 3: SignedProperties (placeholder)
    ref3 = etree.SubElement(si, '{%s}Reference' % NS['ds'])
    ref3.set('Type', SIGNED_PROPS_TYPE)
    ref3.set('URI', f'#{signed_props_id}')
    etree.SubElement(ref3, '{%s}DigestMethod' % NS['ds']).set('Algorithm', SHA256_ALG)
    ref3_dv = etree.SubElement(ref3, '{%s}DigestValue' % NS['ds'])
    ref3_dv.text = 'PLACEHOLDER'

    # SignatureValue placeholder
    sig_val = etree.SubElement(signature, '{%s}SignatureValue' % NS['ds'])
    sig_val.text = 'PLACEHOLDER'

    # KeyInfo
    ki = etree.SubElement(signature, '{%s}KeyInfo' % NS['ds'])
    ki.set('Id', keyinfo_id)
    x509d = etree.SubElement(ki, '{%s}X509Data' % NS['ds'])
    etree.SubElement(x509d, '{%s}X509Certificate' % NS['ds']).text = cert_b64
    if chain:
        etree.SubElement(x509d, '{%s}X509Certificate' % NS['ds']).text = cert_to_base64(chain[0])

    # Object/QualifyingProperties/SignedProperties
    obj = etree.SubElement(signature, '{%s}Object' % NS['ds'])
    qp = etree.SubElement(
        obj,
        '{%s}QualifyingProperties' % NS['xades'],
        nsmap={'xades': NS['xades']}
    )
    qp.set('Target', f'#{sig_id}')

    sp = etree.SubElement(qp, '{%s}SignedProperties' % NS['xades'])
    sp.set('Id', signed_props_id)

    ssp = etree.SubElement(sp, '{%s}SignedSignatureProperties' % NS['xades'])
    etree.SubElement(ssp, '{%s}SigningTime' % NS['xades']).text = signing_time

    sc = etree.SubElement(ssp, '{%s}SigningCertificate' % NS['xades'])

    def add_cert(c, parent):
        ce = etree.SubElement(parent, '{%s}Cert' % NS['xades'])
        cd = etree.SubElement(ce, '{%s}CertDigest' % NS['xades'])
        etree.SubElement(cd, '{%s}DigestMethod' % NS['ds']).set('Algorithm', SHA256_ALG)
        etree.SubElement(cd, '{%s}DigestValue' % NS['ds']).text = cert_digest(c)
        iss = etree.SubElement(ce, '{%s}IssuerSerial' % NS['xades'])
        etree.SubElement(iss, '{%s}X509IssuerName' % NS['ds']).text = get_issuer_dn(c)
        etree.SubElement(iss, '{%s}X509SerialNumber' % NS['ds']).text = str(c.serial_number)

    add_cert(cert, sc)
    if chain:
        add_cert(chain[0], sc)

    spi = etree.SubElement(ssp, '{%s}SignaturePolicyIdentifier' % NS['xades'])
    spid = etree.SubElement(spi, '{%s}SignaturePolicyId' % NS['xades'])
    sigpid = etree.SubElement(spid, '{%s}SigPolicyId' % NS['xades'])
    etree.SubElement(sigpid, '{%s}Identifier' % NS['xades']).text = POLITICA_URL
    sph = etree.SubElement(spid, '{%s}SigPolicyHash' % NS['xades'])
    etree.SubElement(sph, '{%s}DigestMethod' % NS['ds']).set('Algorithm', SHA256_ALG)
    etree.SubElement(sph, '{%s}DigestValue' % NS['ds']).text = POLITICA_HASH

    sr = etree.SubElement(ssp, '{%s}SignerRole' % NS['xades'])
    cr = etree.SubElement(sr, '{%s}ClaimedRoles' % NS['xades'])
    etree.SubElement(cr, '{%s}ClaimedRole' % NS['xades']).text = 'supplier'

    # =========================================================================
    # PASO 3: CALCULAR DIGEST DE KEYINFO usando C14N directo
    # =========================================================================
    keyinfo_c14n = etree.tostring(ki, method='c14n', exclusive=False, with_comments=False)
    keyinfo_digest = sha256_digest(keyinfo_c14n)
    ref2_dv.text = keyinfo_digest

    # =========================================================================
    # PASO 4: CALCULAR DIGEST DE SIGNEDPROPERTIES usando C14N directo
    # =========================================================================
    signedprops_c14n = etree.tostring(sp, method='c14n', exclusive=False, with_comments=False)
    signedprops_digest = sha256_digest(signedprops_c14n)
    ref3_dv.text = signedprops_digest

    # =========================================================================
    # PASO 5: FIRMAR SIGNEDINFO usando C14N directo
    # =========================================================================
    signedinfo_c14n = etree.tostring(si, method='c14n', exclusive=False, with_comments=False)

    # Firmar
    sig_bytes = private_key.sign(
        signedinfo_c14n,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    signature_value = base64.b64encode(sig_bytes).decode('ascii')
    sig_val.text = signature_value

    return invoice
