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
    'ZE02': 'Firma digital invalida',
    'ZE03': 'Certificado no valido',
    'ZE04': 'Certificado expirado',
    'FAJ43a': 'Nombre emisor no informado',
    'FAJ43b': 'Nombre emisor no coincide con RUT',
    'FAJ44a': 'NIT emisor no informado',
    'FAJ44b': 'NIT emisor no coincide con RUT',
    'FAB01': 'XML mal formado',
    'FAB02': 'Namespace incorrecto',
    'FAB03': 'Elemento requerido faltante',
    'FAN01': 'Numero de factura duplicado',
    'FAN02': 'Consecutivo fuera de rango',
    'FAN03': 'Resolucion vencida',
    'FAC01': 'CUFE invalido',
    'FAC02': 'Totales no cuadran',
    'FAC03': 'Impuestos mal calculados',
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
