# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

# Cliente simplificado (nueva implementacion sin zeep)
from .dian_simple import (
    DianSimpleClient,
    DianResponse,
    SendTestSetResponse,
    GetStatusZipResponse,
    SendBillSyncResponse,
    calcular_dv,
    calcular_cufe,
    calcular_cude,
    calcular_software_security_code,
)

# Sistema de tracking de documentos
from .tracker import (
    DocumentTracker,
    TrackedDocument,
    TrackingData,
)

# Cliente legacy (requiere zeep)
try:
    from .dian import (
        DianClient,
        DianSignatureClient,
        Habilitacion,
        GetNumberingRange,
        SendBillAsync,
        SendTestSetAsync,
        SendBillSync,
        GetStatus,
        GetStatusZip,
    )
except ImportError:
    # zeep no esta instalado, solo disponible cliente simplificado
    pass
