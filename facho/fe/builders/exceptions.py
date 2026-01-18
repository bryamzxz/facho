# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Sistema de excepciones para Facho.
Manejo estructurado de errores con codigos DIAN.
"""

from typing import List, Dict, Any, Optional


class FachoError(Exception):
    """Excepcion base para todos los errores de Facho."""

    def __init__(
        self,
        message: str,
        code: str = None,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convertir excepcion a diccionario."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'code': self.code,
            'details': self.details,
        }


class ValidationError(FachoError):
    """Error de validacion de datos."""

    def __init__(
        self,
        message: str,
        errors: List[str] = None,
        field: str = None,
        code: str = "VALIDATION_ERROR"
    ):
        self.errors = errors or []
        self.field = field
        super().__init__(
            message,
            code=code,
            details={'errors': self.errors, 'field': self.field}
        )

    def __str__(self) -> str:
        base = super().__str__()
        if self.errors:
            return f"{base}: {'; '.join(self.errors)}"
        return base


class ConfigurationError(FachoError):
    """Error de configuracion."""

    def __init__(self, message: str, config_key: str = None):
        self.config_key = config_key
        super().__init__(
            message,
            code="CONFIG_ERROR",
            details={'config_key': config_key}
        )


class SignatureError(FachoError):
    """Error en firma digital."""

    def __init__(self, message: str, certificate_info: Dict[str, Any] = None):
        self.certificate_info = certificate_info
        super().__init__(
            message,
            code="SIGNATURE_ERROR",
            details={'certificate_info': certificate_info}
        )


class CertificateError(SignatureError):
    """Error de certificado PKCS#12."""

    def __init__(self, message: str, certificate_path: str = None):
        self.certificate_path = certificate_path
        super().__init__(message, certificate_info={'path': certificate_path})
        self.code = "CERTIFICATE_ERROR"


class DianError(FachoError):
    """Error de comunicacion con DIAN."""

    def __init__(
        self,
        message: str,
        status_code: str = None,
        dian_errors: List[str] = None,
        track_id: str = None,
        cufe: str = None
    ):
        self.status_code = status_code
        self.dian_errors = dian_errors or []
        self.track_id = track_id
        self.cufe = cufe
        super().__init__(
            message,
            code="DIAN_ERROR",
            details={
                'status_code': status_code,
                'dian_errors': self.dian_errors,
                'track_id': track_id,
                'cufe': cufe,
            }
        )

    def __str__(self) -> str:
        base = super().__str__()
        if self.dian_errors:
            return f"{base} - Errores DIAN: {'; '.join(self.dian_errors)}"
        return base


class XmlBuildError(FachoError):
    """Error en construccion de XML."""

    def __init__(self, message: str, element: str = None, reason: str = None):
        self.element = element
        self.reason = reason
        super().__init__(
            message,
            code="XML_BUILD_ERROR",
            details={'element': element, 'reason': reason}
        )


class CufeError(FachoError):
    """Error en calculo de CUFE/CUDE."""

    def __init__(self, message: str, document_number: str = None):
        self.document_number = document_number
        super().__init__(
            message,
            code="CUFE_ERROR",
            details={'document_number': document_number}
        )


class RangeError(ValidationError):
    """Error de rango de numeracion."""

    def __init__(
        self,
        message: str,
        current: int = None,
        range_from: int = None,
        range_to: int = None
    ):
        self.current = current
        self.range_from = range_from
        self.range_to = range_to
        super().__init__(
            message,
            errors=[f"Consecutivo {current} fuera de rango [{range_from}-{range_to}]"],
            code="RANGE_ERROR"
        )


class NetworkError(FachoError):
    """Error de red."""

    def __init__(self, message: str, url: str = None, http_status: int = None):
        self.url = url
        self.http_status = http_status
        super().__init__(
            message,
            code="NETWORK_ERROR",
            details={'url': url, 'http_status': http_status}
        )


class FachoTimeoutError(NetworkError):
    """Error de timeout."""

    def __init__(
        self,
        message: str = "Tiempo de espera agotado",
        timeout_seconds: int = None
    ):
        self.timeout_seconds = timeout_seconds
        super().__init__(message)
        self.code = "TIMEOUT_ERROR"
        self.details['timeout_seconds'] = timeout_seconds


# Codigos de error DIAN conocidos
DIAN_ERROR_CODES = {
    # Errores de firma (ZE)
    'ZE01': 'Firma no encontrada',
    'ZE02': 'Firma digital invalida',
    'ZE03': 'Certificado no valido',
    'ZE04': 'Certificado expirado',
    'ZE05': 'Certificado revocado',
    'ZE06': 'Certificado no corresponde al emisor',

    # Errores de estructura XML (FAB)
    'FAB01': 'XML mal formado',
    'FAB02': 'Namespace incorrecto',
    'FAB03': 'Elemento requerido faltante',
    'FAB04': 'Valor de elemento invalido',
    'FAB05': 'Atributo requerido faltante',

    # Errores de CUFE/CUDE (FAC)
    'FAC01': 'CUFE invalido',
    'FAC02': 'Totales no cuadran',
    'FAC03': 'Impuestos mal calculados',
    'FAC04': 'CUDE invalido',
    'FAC05': 'CUDS invalido',

    # Errores de fecha (FAD)
    'FAD01': 'Fecha emision invalida',
    'FAD02': 'Fecha fuera de periodo autorizado',
    'FAD03': 'Hora emision invalida',
    'FAD04': 'Fecha de vencimiento invalida',

    # Errores de emisor (FAJ)
    'FAJ43a': 'Nombre emisor no informado',
    'FAJ43b': 'Nombre emisor no coincide con RUT',
    'FAJ44a': 'NIT emisor no informado',
    'FAJ44b': 'NIT emisor no coincide con RUT',
    'FAJ45': 'Direccion emisor no informada',
    'FAJ46': 'Municipio emisor invalido',

    # Errores de numeracion (FAN)
    'FAN01': 'Numero de factura duplicado',
    'FAN02': 'Consecutivo fuera de rango',
    'FAN03': 'Resolucion vencida',
    'FAN04': 'Prefijo no corresponde a resolucion',
    'FAN05': 'Resolucion no encontrada',

    # Errores de notas credito/debito (NC/ND)
    'NCB01': 'Factura referenciada no existe',
    'NCB02': 'CUFE de factura referenciada invalido',
    'NCB03': 'Fecha de factura referenciada invalida',
    'NCB04': 'Codigo de respuesta invalido',
    'NDB01': 'Factura referenciada no existe',
    'NDB02': 'CUFE de factura referenciada invalido',

    # Errores de documento soporte (DS)
    'DSB01': 'Proveedor no valido para documento soporte',
    'DSB02': 'Regimen fiscal del proveedor invalido',
    'DSB03': 'CUDS invalido',

    # Errores de adquiriente (FAK)
    'FAK01': 'NIT adquiriente no informado',
    'FAK02': 'Nombre adquiriente no informado',
    'FAK03': 'Tipo documento adquiriente invalido',

    # Errores de lineas (FAL)
    'FAL01': 'Cantidad debe ser mayor a cero',
    'FAL02': 'Precio unitario invalido',
    'FAL03': 'Descripcion de producto requerida',
    'FAL04': 'Codigo de producto invalido',

    # Errores de software (SFT)
    'SFT01': 'Software ID invalido',
    'SFT02': 'Software PIN invalido',
    'SFT03': 'Software Security Code invalido',
}


def get_dian_error_description(code: str) -> str:
    """Obtener descripcion de un codigo de error DIAN."""
    return DIAN_ERROR_CODES.get(code, f"Error DIAN: {code}")


def parse_dian_errors(error_messages: List[str]) -> List[Dict[str, str]]:
    """Parsear mensajes de error DIAN."""
    parsed = []
    for msg in error_messages:
        if ':' in msg:
            code, description = msg.split(':', 1)
            code = code.strip()
            description = description.strip()
        else:
            code = None
            description = msg

        parsed.append({
            'code': code,
            'message': description,
            'known_error': code in DIAN_ERROR_CODES if code else False,
            'suggestion': DIAN_ERROR_CODES.get(code, '') if code else '',
        })

    return parsed


# =============================================================================
# EXCEPCIONES ESPECIFICAS
# =============================================================================

class CertificateExpiredError(CertificateError):
    """Error de certificado expirado."""

    def __init__(self, message: str, expiry_date: str = None):
        super().__init__(message)
        self.code = "ZE04"
        self.expiry_date = expiry_date


class CertificateRevokedError(CertificateError):
    """Error de certificado revocado."""

    def __init__(self, message: str, revocation_date: str = None):
        super().__init__(message)
        self.code = "ZE05"
        self.revocation_date = revocation_date


class DuplicateInvoiceError(DianError):
    """Error de factura duplicada."""

    def __init__(self, invoice_number: str, existing_cufe: str = None):
        super().__init__(
            f"Factura {invoice_number} ya existe en DIAN",
            status_code='FAN01',
            dian_errors=[f"Documento duplicado: {invoice_number}"]
        )
        self.invoice_number = invoice_number
        self.existing_cufe = existing_cufe


class ResolutionExpiredError(ValidationError):
    """Error de resolucion vencida."""

    def __init__(self, resolution_number: str, end_date: str):
        super().__init__(
            f"Resolucion {resolution_number} vencio el {end_date}",
            errors=[f"Resolucion vencida: {end_date}"],
            code="FAN03"
        )
        self.resolution_number = resolution_number
        self.end_date = end_date


class ResolutionNotFoundError(ValidationError):
    """Error de resolucion no encontrada."""

    def __init__(self, resolution_number: str):
        super().__init__(
            f"Resolucion {resolution_number} no encontrada",
            errors=[f"Resolucion no encontrada: {resolution_number}"],
            code="FAN05"
        )
        self.resolution_number = resolution_number


class CufeValidationError(CufeError):
    """Error de validacion de CUFE."""

    def __init__(self, cufe: str, expected_length: int = 96):
        actual_length = len(cufe) if cufe else 0
        super().__init__(
            f"CUFE invalido: esperado {expected_length} caracteres, "
            f"recibido {actual_length}",
            document_number=None
        )
        self.cufe = cufe
        self.expected_length = expected_length
        self.actual_length = actual_length


class ReferenceNotFoundError(DianError):
    """Error de referencia de factura no encontrada (para notas)."""

    def __init__(
        self,
        invoice_number: str,
        invoice_cufe: str = None,
        doc_type: str = 'nota credito'
    ):
        super().__init__(
            f"Factura referenciada {invoice_number} no existe en DIAN",
            status_code='NCB01' if doc_type == 'nota credito' else 'NDB01',
            dian_errors=[f"Factura referenciada no existe: {invoice_number}"]
        )
        self.invoice_number = invoice_number
        self.invoice_cufe = invoice_cufe
        self.doc_type = doc_type


class TotalsValidationError(ValidationError):
    """Error de validacion de totales."""

    def __init__(
        self,
        expected: float,
        actual: float,
        field: str = "total"
    ):
        diff = abs(expected - actual)
        super().__init__(
            f"Totales no cuadran: {field}",
            errors=[
                f"Valor esperado: {expected:.2f}",
                f"Valor actual: {actual:.2f}",
                f"Diferencia: {diff:.2f}"
            ],
            field=field,
            code="FAC02"
        )
        self.expected = expected
        self.actual = actual
        self.difference = diff


class UvtLimitExceededError(ValidationError):
    """Error de limite UVT excedido (para documentos POS)."""

    def __init__(self, total: float, uvt_limit: int, uvt_value: float):
        max_value = uvt_limit * uvt_value
        super().__init__(
            f"Total ${total:,.2f} excede limite de {uvt_limit} UVT "
            f"(${max_value:,.2f})",
            errors=[f"Limite POS excedido: {total:.2f} > {max_value:.2f}"],
            code="POS_LIMIT_EXCEEDED"
        )
        self.total = total
        self.uvt_limit = uvt_limit
        self.uvt_value = uvt_value
        self.max_value = max_value


def create_dian_exception(error_code: str, message: str = None) -> FachoError:
    """
    Crear excepcion apropiada basada en codigo de error DIAN.

    Args:
        error_code: Codigo de error DIAN (ej: 'ZE04', 'FAN01')
        message: Mensaje adicional (opcional)

    Returns:
        Excepcion apropiada para el codigo de error
    """
    description = DIAN_ERROR_CODES.get(error_code, f"Error DIAN: {error_code}")
    full_message = f"{description}: {message}" if message else description

    # Mapear codigos a excepciones especificas
    if error_code == 'ZE04':
        return CertificateExpiredError(full_message)
    elif error_code == 'ZE05':
        return CertificateRevokedError(full_message)
    elif error_code in ('ZE01', 'ZE02', 'ZE03', 'ZE06'):
        return SignatureError(full_message)
    elif error_code == 'FAN01':
        return DuplicateInvoiceError("", None)
    elif error_code == 'FAN03':
        return ResolutionExpiredError("", "")
    elif error_code in ('NCB01', 'NCB02', 'NDB01', 'NDB02'):
        return ReferenceNotFoundError("")
    elif error_code in ('FAC01', 'FAC04', 'FAC05'):
        return CufeError(full_message)
    elif error_code == 'FAC02':
        return TotalsValidationError(0, 0)
    else:
        return DianError(full_message, status_code=error_code)
