# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constantes para generacion de documentos UBL 2.1 DIAN.
"""

# Namespaces UBL 2.1
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

# Atributos estandar para schemeAgency
SCHEME_AGENCY_ATTRS = {
    'schemeAgencyName': 'CO, DIAN (Direccion de Impuestos y Aduanas Nacionales)',
    'schemeAgencyID': '195'
}

# Constantes DIAN
DIAN_UBL_VERSION = 'UBL 2.1'
DIAN_CUSTOMIZATION_ID = '10'
DIAN_PROFILE_ID = 'DIAN 2.1: Factura Electronica de Venta'
DIAN_PROFILE_ID_CREDIT_NOTE = 'DIAN 2.1: Nota Credito de Factura Electronica de Venta'
DIAN_PROFILE_ID_DEBIT_NOTE = 'DIAN 2.1: Nota Debito de Factura Electronica de Venta'

# Codigos de tipo de documento
INVOICE_TYPE_CODE = '01'  # Factura de venta
CREDIT_NOTE_TYPE_CODE = '91'  # Nota credito
DEBIT_NOTE_TYPE_CODE = '92'  # Nota debito

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

# Atributos para IdentificationCode de pais
COUNTRY_ID_ATTRS = {
    'listAgencyID': '6',
    'listAgencyName': 'United Nations Economic Commission for Europe',
    'listSchemeURI': 'urn:oasis:names:specification:ubl:codelist:gc:CountryIdentificationCode-2.1',
}

# ID del proveedor de autorizacion (DIAN)
AUTHORIZATION_PROVIDER_ID = '800197268'

# CustomizationID por tipo de documento
CUSTOMIZATION_ID_INVOICE = '10'
CUSTOMIZATION_ID_CREDIT_NOTE = '20'
CUSTOMIZATION_ID_DEBIT_NOTE = '30'

# Motivos para notas credito (ResponseCode)
CREDIT_REASONS = {
    '1': 'Devolucion parcial de los bienes y/o no aceptacion parcial del servicio',
    '2': 'Anulacion de factura electronica',
    '3': 'Rebaja o descuento parcial o total',
    '4': 'Ajuste de precio',
}

# Motivos para notas debito (ResponseCode)
DEBIT_REASONS = {
    '1': 'Intereses',
    '2': 'Gastos por cobrar',
    '3': 'Cambio del valor',
    '4': 'Otros',
}

# Tipos de documento soportados
DOC_TYPES = {
    'factura': {
        'code': INVOICE_TYPE_CODE,
        'prefix_file': 'fv',
        'root_element': 'Invoice',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'profile_id': DIAN_PROFILE_ID,
        'uuid_name': 'CUFE-SHA384',
        'customization_id': CUSTOMIZATION_ID_INVOICE,
    },
    'credito': {
        'code': CREDIT_NOTE_TYPE_CODE,
        'prefix_file': 'nc',
        'root_element': 'CreditNote',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2',
        'profile_id': DIAN_PROFILE_ID_CREDIT_NOTE,
        'uuid_name': 'CUDE-SHA384',
        'customization_id': CUSTOMIZATION_ID_CREDIT_NOTE,
    },
    'debito': {
        'code': DEBIT_NOTE_TYPE_CODE,
        'prefix_file': 'nd',
        'root_element': 'DebitNote',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2',
        'profile_id': DIAN_PROFILE_ID_DEBIT_NOTE,
        'uuid_name': 'CUDE-SHA384',
        'customization_id': CUSTOMIZATION_ID_DEBIT_NOTE,
    },
}

# =============================================================================
# TIPOS DE DOCUMENTO ADICIONALES
# =============================================================================

# Codigos de tipo de documento adicionales
EXPORT_INVOICE_TYPE_CODE = '02'
POS_INVOICE_TYPE_CODE = '03'
CONTINGENCY_INVOICE_TYPE_CODE = '04'
SUPPORT_DOCUMENT_TYPE_CODE = '05'

# ProfileIDs adicionales
DIAN_PROFILE_ID_EXPORT = 'DIAN 2.1: Factura Electronica de Exportacion'
DIAN_PROFILE_ID_CONTINGENCY = 'DIAN 2.1: Factura Electronica de Contingencia'
DIAN_PROFILE_ID_SUPPORT = (
    'DIAN 2.1: documento soporte en adquisiciones efectuadas '
    'a no obligados a facturar'
)

# CustomizationIDs adicionales
CUSTOMIZATION_ID_EXPORT = '02'
CUSTOMIZATION_ID_CONTINGENCY = '04'
CUSTOMIZATION_ID_SUPPORT = '05'

# =============================================================================
# INCOTERMS Y MONEDAS
# =============================================================================

# Incoterms para factura de exportacion
INCOTERMS = {
    'EXW': 'Ex Works',
    'FCA': 'Free Carrier',
    'FAS': 'Free Alongside Ship',
    'FOB': 'Free On Board',
    'CFR': 'Cost and Freight',
    'CIF': 'Cost, Insurance and Freight',
    'CPT': 'Carriage Paid To',
    'CIP': 'Carriage and Insurance Paid To',
    'DAP': 'Delivered at Place',
    'DPU': 'Delivered at Place Unloaded',
    'DDP': 'Delivered Duty Paid',
}

# Monedas soportadas
CURRENCIES = {
    'COP': 'Peso Colombiano',
    'USD': 'Dolar Estadounidense',
    'EUR': 'Euro',
    'GBP': 'Libra Esterlina',
    'JPY': 'Yen Japones',
    'CHF': 'Franco Suizo',
    'CAD': 'Dolar Canadiense',
    'MXN': 'Peso Mexicano',
    'BRL': 'Real Brasileno',
}

# =============================================================================
# CODIGOS DE RAZON PARA DESCUENTOS Y CARGOS
# =============================================================================

# Codigos de razon de descuento DIAN
ALLOWANCE_REASON_CODES = {
    '00': 'Descuento no especificado',
    '01': 'Descuento por pronto pago',
    '02': 'Descuento por volumen',
    '03': 'Descuento especial',
    '04': 'Descuento comercial',
}

# Codigos de razon de cargo DIAN
CHARGE_REASON_CODES = {
    '00': 'Cargo no especificado',
    '01': 'Flete',
    '02': 'Empaque',
    '03': 'Seguros',
    '04': 'Otros cargos',
}

# =============================================================================
# ALGORITMOS DE FIRMA DIGITAL
# =============================================================================

# Canonicalizacion
C14N_ALG = 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
C14N_EXC_ALG = 'http://www.w3.org/2001/10/xml-exc-c14n#'

# Transformaciones
ENVELOPED_SIG = 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'

# Algoritmos RSA
RSA_SHA256 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
RSA_SHA384 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha384'
RSA_SHA512 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha512'

# Algoritmos SHA
SHA256_ALG = 'http://www.w3.org/2001/04/xmlenc#sha256'
SHA384_ALG = 'http://www.w3.org/2001/04/xmldsig-more#sha384'
SHA512_ALG = 'http://www.w3.org/2001/04/xmldsig-more#sha512'

# Tipo SignedProperties XAdES
SIGNED_PROPS_TYPE = 'http://uri.etsi.org/01903#SignedProperties'

# =============================================================================
# POLITICA DE FIRMA DIAN
# =============================================================================

POLITICA_URL = 'https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf'
POLITICA_HASH = 'dMoMvtcG5aIzgYo0tIsSQeVJBDnUnfSOfBpxXrmor0Y='
POLITICA_NAME = 'Politica de firma para facturas electronicas de la Republica de Colombia.'

# =============================================================================
# NAMESPACES SOAP WS-SECURITY
# =============================================================================

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
# ENDPOINTS DIAN
# =============================================================================

DIAN_ENDPOINTS = {
    'produccion': 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc',
    'habilitacion': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
}

# =============================================================================
# IMPUESTOS ADICIONALES v1.9
# =============================================================================

TAX_CODES_EXTENDED = {
    'INPP': '32',    # Impuesto Nacional Productos Plasticos
    'IBUA': '33',    # Impuesto Bebidas Ultraprocesadas Azucaradas
    'ICUI': '34',    # Impuesto Comestibles Ultraprocesados
    'ICL': '35',     # Impuesto al Consumo de Licores
    'ADV': '36',     # Ad Valorem
}

# =============================================================================
# TIPOS DE DOCUMENTO COMPLETOS (DOC_TYPES_FULL)
# =============================================================================

DOC_TYPES_FULL = {
    # Facturas
    'FA': {
        'code': '01',
        'root_element': 'Invoice',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'customization_id': '10',
        'profile_id': 'DIAN 2.1: Factura Electronica de Venta',
        'uuid_scheme': 'CUFE-SHA384',
        'uses_technical_key': True,
        'file_prefix': 'fv',
        'quantity_element': 'InvoicedQuantity',
        'line_element': 'InvoiceLine',
        'total_element': 'LegalMonetaryTotal',
    },
    'EX': {
        'code': '02',
        'root_element': 'Invoice',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'customization_id': '02',
        'profile_id': 'DIAN 2.1: Factura Electronica de Exportacion',
        'uuid_scheme': 'CUFE-SHA384',
        'uses_technical_key': True,
        'file_prefix': 'fv',
        'tax_exempt': True,
        'quantity_element': 'InvoicedQuantity',
        'line_element': 'InvoiceLine',
        'total_element': 'LegalMonetaryTotal',
    },
    'PO': {
        'code': '03',
        'root_element': 'Invoice',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'customization_id': '10',
        'profile_id': 'DIAN 2.1: Factura Electronica de Venta',
        'uuid_scheme': 'CUDE-SHA384',
        'uses_technical_key': False,
        'file_prefix': 'fv',
        'uvt_limit': 5,
        'quantity_element': 'InvoicedQuantity',
        'line_element': 'InvoiceLine',
        'total_element': 'LegalMonetaryTotal',
    },
    'CO': {
        'code': '04',
        'root_element': 'Invoice',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'customization_id': '04',
        'profile_id': 'DIAN 2.1: Factura Electronica de Contingencia',
        'uuid_scheme': 'CUFE-SHA384',
        'uses_technical_key': True,
        'file_prefix': 'fv',
        'is_contingency': True,
        'quantity_element': 'InvoicedQuantity',
        'line_element': 'InvoiceLine',
        'total_element': 'LegalMonetaryTotal',
    },
    # Notas
    'NC': {
        'code': '91',
        'root_element': 'CreditNote',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2',
        'customization_id': '20',
        'profile_id': 'DIAN 2.1: Nota Credito de Factura Electronica de Venta',
        'uuid_scheme': 'CUDE-SHA384',
        'uses_technical_key': False,
        'file_prefix': 'nc',
        'requires_reference': True,
        'quantity_element': 'CreditedQuantity',
        'line_element': 'CreditNoteLine',
        'total_element': 'LegalMonetaryTotal',
    },
    'ND': {
        'code': '92',
        'root_element': 'DebitNote',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2',
        'customization_id': '30',
        'profile_id': 'DIAN 2.1: Nota Debito de Factura Electronica de Venta',
        'uuid_scheme': 'CUDE-SHA384',
        'uses_technical_key': False,
        'file_prefix': 'nd',
        'requires_reference': True,
        'quantity_element': 'DebitedQuantity',
        'line_element': 'DebitNoteLine',
        'total_element': 'RequestedMonetaryTotal',
    },
    # Documento Soporte
    'DS': {
        'code': '05',
        'root_element': 'Invoice',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'customization_id': '05',
        'profile_id': 'DIAN 2.1: documento soporte en adquisiciones efectuadas a no obligados a facturar',
        'uuid_scheme': 'CUDS-SHA384',
        'uses_technical_key': False,
        'file_prefix': 'ds',
        'quantity_element': 'InvoicedQuantity',
        'line_element': 'InvoiceLine',
        'total_element': 'LegalMonetaryTotal',
    },
    'NA': {
        'code': '95',
        'root_element': 'Invoice',
        'namespace': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'customization_id': '05',
        'profile_id': 'DIAN 2.1: documento soporte en adquisiciones efectuadas a no obligados a facturar',
        'uuid_scheme': 'CUDS-SHA384',
        'uses_technical_key': False,
        'file_prefix': 'ds',
        'requires_reference': True,
        'quantity_element': 'InvoicedQuantity',
        'line_element': 'InvoiceLine',
        'total_element': 'LegalMonetaryTotal',
    },
}

# =============================================================================
# CODIGOS DE RESPUESTA PARA NOTAS
# =============================================================================

# Codigos de respuesta para Nota Credito (DiscrepancyResponse)
CREDIT_NOTE_RESPONSE_CODES = {
    '1': 'Devolucion parcial de los bienes y/o no aceptacion parcial del servicio',
    '2': 'Anulacion de factura electronica',
    '3': 'Rebaja o descuento parcial o total',
    '4': 'Ajuste de precio',
    '5': 'Otros',
}

# Codigos de respuesta para Nota Debito
DEBIT_NOTE_RESPONSE_CODES = {
    '1': 'Intereses',
    '2': 'Gastos por cobrar',
    '3': 'Cambio del valor',
    '4': 'Otros',
}

# =============================================================================
# REGIMEN FISCAL
# =============================================================================

TAX_REGIMES = {
    'RESPONSABLE_IVA': '48',
    'NO_RESPONSABLE_IVA': '49',
    'NO_RESPONSABLE_PN': 'R-99-PN',
}

# =============================================================================
# CONSUMIDOR FINAL GENERICO
# =============================================================================

GENERIC_CONSUMER = {
    'nit': '222222222222',
    'name': 'CONSUMIDOR FINAL',
    'doc_type': '13',  # Cedula de ciudadania
}

# =============================================================================
# VALOR UVT POR ANO
# =============================================================================

UVT_VALUES = {
    2023: 42412,
    2024: 47065,
    2025: 49799,
    2026: 52500,  # Estimado
}

# =============================================================================
# TIPOS DE DOCUMENTO DE IDENTIFICACION
# =============================================================================

ID_TYPES = {
    '11': 'Registro civil',
    '12': 'Tarjeta de identidad',
    '13': 'Cedula de ciudadania',
    '21': 'Tarjeta de extranjeria',
    '22': 'Cedula de extranjeria',
    '31': 'NIT',
    '41': 'Pasaporte',
    '42': 'Tipo de documento extranjero',
    '47': 'PEP',
    '50': 'NIT de otro pais',
    '91': 'NUIP',
}
