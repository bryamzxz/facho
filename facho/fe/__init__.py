# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

# Nuevos modulos simplificados (implementacion funcional DIAN)
# Estos no requieren dependencias legacy
from . import signing
from . import builders

# Importaciones legacy (requieren xmlsig, xades, zeep, etc.)
try:
    from .fe import FeXML
    from .fe import fe_from_string
    from .fe import NAMESPACES
    from .fe import DianXMLExtensionSigner
    from .fe import DianXMLExtensionSoftwareSecurityCode
    from .fe import DianXMLExtensionCUFE
    from .fe import DianXMLExtensionCUDE
    from .fe import DianXMLExtensionCUDS
    from .fe import DianXMLExtensionInvoiceAuthorization
    from .fe import DianXMLExtensionSoftwareProvider
    from .fe import DianXMLExtensionAuthorizationProvider
    from .fe import DianZIP
    from .fe import AMBIENTE_PRUEBAS
    from .fe import AMBIENTE_PRODUCCION
    from . import form_xml
    from . import nomina
except ImportError:
    # Dependencias legacy no instaladas (xmlsig, xades)
    # Solo disponibles los modulos simplificados
    pass
