# This file is part of dian_fe.
"""
Configuracion y constantes para facturacion electronica DIAN Colombia.
Compatible con Anexo Tecnico v1.9.
"""

from typing import Dict, Any

# =============================================================================
# NAMESPACES UBL 2.1
# =============================================================================

NS = {
    'fe': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
    'nc': 'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2',
    'nd': 'urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xades': 'http://uri.etsi.org/01903/v1.3.2#',
    'xades141': 'http://uri.etsi.org/01903/v1.4.1#',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
}

# Namespaces SOAP para WS-Security
NS_SOAP = {
    'soap': 'http://www.w3.org/2003/05/soap-envelope',
    'wcf': 'http://wcf.dian.colombia',
    'wsa': 'http://www.w3.org/2005/08/addressing',
    'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
    'wsu': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd',
    'ec': 'http://www.w3.org/2001/10/xml-exc-c14n#',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
}

# =============================================================================
# ALGORITMOS DE FIRMA
# =============================================================================

C14N_ALG = 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
C14N_EXC_ALG = 'http://www.w3.org/2001/10/xml-exc-c14n#'
RSA_SHA256 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
SHA256_ALG = 'http://www.w3.org/2001/04/xmlenc#sha256'
ENVELOPED_SIG = 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
SIGNED_PROPS_TYPE = 'http://uri.etsi.org/01903#SignedProperties'

# =============================================================================
# POLITICA DE FIRMA DIAN v2
# =============================================================================

POLITICA_URL = 'https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf'
POLITICA_HASH = 'dMoMvtcG5aIzgYo0tIsSQeVJBDnUnfSOfBpxXrmor0Y='
POLITICA_NAME = 'Politica de firma para facturas electronicas de la Republica de Colombia.'

# =============================================================================
# ENDPOINTS DIAN
# =============================================================================

ENDPOINT_HABILITACION = 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc'
ENDPOINT_PRODUCCION = 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc'

# =============================================================================
# CONSTANTES DIAN
# =============================================================================

DIAN_UBL_VERSION = 'UBL 2.1'
DIAN_CUSTOMIZATION_ID = '10'
DIAN_PROFILE_ID = 'DIAN 2.1: Factura Electronica de Venta'
DIAN_PROFILE_ID_CREDIT_NOTE = 'DIAN 2.1: Nota Credito de Factura Electronica de Venta'
DIAN_PROFILE_ID_DEBIT_NOTE = 'DIAN 2.1: Nota Debito de Factura Electronica de Venta'

# Codigos de tipo de documento
INVOICE_TYPE_CODE = '01'
CREDIT_NOTE_TYPE_CODE = '91'
DEBIT_NOTE_TYPE_CODE = '92'

# CustomizationID por tipo de documento
CUSTOMIZATION_ID_INVOICE = '10'
CUSTOMIZATION_ID_CREDIT_NOTE = '20'
CUSTOMIZATION_ID_DEBIT_NOTE = '30'

# Atributos estandar para schemeAgency
SCHEME_AGENCY_ATTRS = {
    'schemeAgencyName': 'CO, DIAN (Direccion de Impuestos y Aduanas Nacionales)',
    'schemeAgencyID': '195'
}

# Atributos para IdentificationCode de pais
COUNTRY_ID_ATTRS = {
    'listAgencyID': '6',
    'listAgencyName': 'United Nations Economic Commission for Europe',
    'listSchemeURI': 'urn:oasis:names:specification:ubl:codelist:gc:CountryIdentificationCode-2.1',
}

# ID del proveedor de autorizacion (DIAN)
AUTHORIZATION_PROVIDER_ID = '800197268'

# =============================================================================
# TIPOS DE DOCUMENTO
# =============================================================================

DOC_TYPES = {
    'factura': {
        'code': INVOICE_TYPE_CODE,
        'prefix_file': 'fv',
        'root_element': 'Invoice',
        'namespace': NS['fe'],
        'profile_id': DIAN_PROFILE_ID,
        'uuid_name': 'CUFE-SHA384',
        'customization_id': CUSTOMIZATION_ID_INVOICE,
    },
    'credito': {
        'code': CREDIT_NOTE_TYPE_CODE,
        'prefix_file': 'nc',
        'root_element': 'CreditNote',
        'namespace': NS['nc'],
        'profile_id': DIAN_PROFILE_ID_CREDIT_NOTE,
        'uuid_name': 'CUDE-SHA384',
        'customization_id': CUSTOMIZATION_ID_CREDIT_NOTE,
    },
    'debito': {
        'code': DEBIT_NOTE_TYPE_CODE,
        'prefix_file': 'nd',
        'root_element': 'DebitNote',
        'namespace': NS['nd'],
        'profile_id': DIAN_PROFILE_ID_DEBIT_NOTE,
        'uuid_name': 'CUDE-SHA384',
        'customization_id': CUSTOMIZATION_ID_DEBIT_NOTE,
    },
}

# =============================================================================
# CODIGOS DE MOTIVO
# =============================================================================

CREDIT_REASONS = {
    '1': 'Devolucion parcial de los bienes y/o no aceptacion parcial del servicio',
    '2': 'Anulacion de factura electronica',
    '3': 'Rebaja o descuento parcial o total',
    '4': 'Ajuste de precio',
}

DEBIT_REASONS = {
    '1': 'Intereses',
    '2': 'Gastos por cobrar',
    '3': 'Cambio del valor',
    '4': 'Otros',
}

# Codigos de impuesto
TAX_CODES = {
    'IVA': '01',
    'IC': '02',
    'ICA': '03',
    'INC': '04',
    'ReteIVA': '05',
    'ReteFte': '06',
    'ReteICA': '07',
}

# =============================================================================
# CONFIGURACION GLOBAL
# =============================================================================

CONFIG: Dict[str, Any] = {}


def set_config(config: Dict[str, Any]) -> None:
    """Establecer configuracion global."""
    global CONFIG
    CONFIG.update(config)


def get_config() -> Dict[str, Any]:
    """Obtener configuracion global."""
    return CONFIG
