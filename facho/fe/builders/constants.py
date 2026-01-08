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
