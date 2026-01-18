# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Sistema de validacion para documentos electronicos DIAN.
"""

import re
from datetime import datetime
from typing import List, Any, Optional

from .exceptions import ValidationError, RangeError


# Expresiones regulares
NIT_PATTERN = re.compile(r'^\d{9,10}$')
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
TIME_PATTERN = re.compile(r'^\d{2}:\d{2}:\d{2}-05:00$')
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)
POSTAL_CODE_PATTERN = re.compile(r'^\d{6}$')
MUNICIPALITY_CODE_PATTERN = re.compile(r'^\d{5}$')


def validate_nit(nit: str, field_name: str = "NIT") -> List[str]:
    """Validar NIT colombiano."""
    errors = []
    if not nit:
        errors.append(f"{field_name} es requerido")
        return errors
    nit_clean = nit.replace('-', '').replace(' ', '').strip()
    if not NIT_PATTERN.match(nit_clean):
        errors.append(f"{field_name} debe tener 9-10 digitos (recibido: {nit})")
    return errors


def validate_date(fecha: str, field_name: str = "Fecha") -> List[str]:
    """Validar formato de fecha DIAN (YYYY-MM-DD)."""
    errors = []
    if not fecha:
        errors.append(f"{field_name} es requerida")
        return errors
    if not DATE_PATTERN.match(fecha):
        errors.append(
            f"{field_name} debe tener formato YYYY-MM-DD (recibido: {fecha})"
        )
        return errors
    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        errors.append(f"{field_name} no es una fecha valida: {fecha}")
    return errors


def validate_time(hora: str, field_name: str = "Hora") -> List[str]:
    """Validar formato de hora DIAN (HH:MM:SS-05:00)."""
    errors = []
    if not hora:
        errors.append(f"{field_name} es requerida")
        return errors
    if not TIME_PATTERN.match(hora):
        errors.append(
            f"{field_name} debe tener formato HH:MM:SS-05:00 (recibido: {hora})"
        )
    return errors


def validate_uuid(uuid_str: str, field_name: str = "UUID") -> List[str]:
    """Validar formato UUID."""
    errors = []
    if not uuid_str:
        errors.append(f"{field_name} es requerido")
        return errors
    if not UUID_PATTERN.match(uuid_str):
        errors.append(f"{field_name} no tiene formato UUID valido: {uuid_str}")
    return errors


def validate_not_empty(value: str, field_name: str) -> List[str]:
    """Validar que un string no este vacio."""
    if not value or not str(value).strip():
        return [f"{field_name} es requerido"]
    return []


def validate_positive_number(
    value: float,
    field_name: str,
    allow_zero: bool = True
) -> List[str]:
    """Validar que un numero sea positivo."""
    errors = []
    if value is None:
        errors.append(f"{field_name} es requerido")
        return errors
    if allow_zero:
        if value < 0:
            errors.append(
                f"{field_name} no puede ser negativo (recibido: {value})"
            )
    else:
        if value <= 0:
            errors.append(
                f"{field_name} debe ser mayor que cero (recibido: {value})"
            )
    return errors


class ConfigValidator:
    """Validador de configuracion de facturacion."""

    def validate(self, config: Any) -> List[str]:
        """Validar configuracion."""
        errors = []

        # Software
        errors.extend(validate_uuid(
            getattr(config, 'software_id', None), "Software ID"
        ))
        errors.extend(validate_not_empty(
            getattr(config, 'software_pin', None), "Software PIN"
        ))
        errors.extend(validate_not_empty(
            getattr(config, 'technical_key', None), "Clave tecnica"
        ))

        # Empresa
        errors.extend(validate_nit(
            getattr(config, 'nit', None), "NIT empresa"
        ))
        errors.extend(validate_not_empty(
            getattr(config, 'company_name', None), "Nombre empresa"
        ))

        # Resolucion
        errors.extend(validate_not_empty(
            getattr(config, 'resolution_number', None), "Numero de resolucion"
        ))
        errors.extend(validate_date(
            getattr(config, 'resolution_date', None), "Fecha inicio resolucion"
        ))
        errors.extend(validate_date(
            getattr(config, 'resolution_end_date', None), "Fecha fin resolucion"
        ))

        # Rangos
        errors.extend(validate_not_empty(
            getattr(config, 'range_from', None), "Rango desde"
        ))
        errors.extend(validate_not_empty(
            getattr(config, 'range_to', None), "Rango hasta"
        ))

        # Ambiente
        environment = getattr(config, 'environment', None)
        if environment not in ('1', '2'):
            errors.append("Ambiente debe ser '1' (produccion) o '2' (pruebas)")

        return errors


class PartyValidator:
    """Validador de datos de parte (emisor/receptor)."""

    def validate(self, party: Any, party_type: str = "Parte") -> List[str]:
        """Validar datos de una parte."""
        errors = []
        if party is None:
            errors.append(f"{party_type} es requerido")
            return errors

        # Documento de identificacion
        scheme_name = getattr(party, 'scheme_name', '31')
        nit = getattr(party, 'nit', None)
        if scheme_name == '31':
            errors.extend(validate_nit(nit, f"NIT {party_type}"))
        else:
            errors.extend(validate_not_empty(nit, f"Documento {party_type}"))

        # Nombres
        errors.extend(validate_not_empty(
            getattr(party, 'name', None), f"Nombre {party_type}"
        ))
        errors.extend(validate_not_empty(
            getattr(party, 'legal_name', None), f"Razon social {party_type}"
        ))

        # Tipo de organizacion
        org_code = getattr(party, 'organization_code', None)
        if org_code not in ('1', '2'):
            errors.append(
                f"Tipo organizacion {party_type} debe ser "
                "'1' (juridica) o '2' (natural)"
            )

        # Direccion
        address = getattr(party, 'address', None)
        if address:
            if not getattr(address, 'city_code', None):
                errors.append(f"Codigo municipio {party_type} es requerido")
            errors.extend(validate_not_empty(
                getattr(address, 'city_name', None), f"Ciudad {party_type}"
            ))
            errors.extend(validate_not_empty(
                getattr(address, 'address_line', None), f"Direccion {party_type}"
            ))
        else:
            errors.append(f"Direccion {party_type} es requerida")

        return errors


class InvoiceLineValidator:
    """Validador de lineas de factura."""

    def validate(self, lines: List[Any]) -> List[str]:
        """Validar lineas de factura."""
        errors = []
        if not lines:
            errors.append("Factura debe tener al menos una linea")
            return errors

        for i, line in enumerate(lines, 1):
            prefix = f"Linea {i}"

            errors.extend(validate_not_empty(
                getattr(line, 'description', None), f"{prefix} descripcion"
            ))
            errors.extend(validate_positive_number(
                getattr(line, 'quantity', None),
                f"{prefix} cantidad",
                allow_zero=False
            ))
            errors.extend(validate_positive_number(
                getattr(line, 'unit_price', None),
                f"{prefix} precio unitario",
                allow_zero=True
            ))
            errors.extend(validate_not_empty(
                getattr(line, 'unit_code', None), f"{prefix} codigo unidad"
            ))

        return errors


class InvoiceValidator:
    """Validador completo de factura."""

    def __init__(self):
        self.config_validator = ConfigValidator()
        self.party_validator = PartyValidator()
        self.line_validator = InvoiceLineValidator()

    def validate(self, data: Any, config: Any) -> List[str]:
        """Validar factura completa."""
        errors = []

        # Validar configuracion
        config_errors = self.config_validator.validate(config)
        if config_errors:
            errors.extend([f"Config: {e}" for e in config_errors])

        # Numero de documento
        errors.extend(validate_not_empty(
            getattr(data, 'number', None), "Numero de factura"
        ))

        # Fechas
        errors.extend(validate_date(
            getattr(data, 'issue_date', None), "Fecha emision"
        ))
        errors.extend(validate_time(
            getattr(data, 'issue_time', None), "Hora emision"
        ))

        due_date = getattr(data, 'due_date', None)
        if due_date:
            errors.extend(validate_date(due_date, "Fecha vencimiento"))

        # Partes
        supplier = getattr(data, 'supplier', None)
        customer = getattr(data, 'customer', None)
        errors.extend(self.party_validator.validate(supplier, "Emisor"))
        errors.extend(self.party_validator.validate(customer, "Adquiriente"))

        # Lineas
        lines = getattr(data, 'lines', [])
        errors.extend(self.line_validator.validate(lines))

        # Validar consecutivo en rango
        number = getattr(data, 'number', None)
        range_from = getattr(config, 'range_from', None)
        range_to = getattr(config, 'range_to', None)

        if number and range_from and range_to:
            try:
                prefix = getattr(config, 'prefix', '') or ''
                num_str = str(number).replace(prefix, '').strip()
                if not num_str.isdigit():
                    num_str = ''.join(filter(str.isdigit, num_str))
                if num_str:
                    current = int(num_str)
                    from_val = int(range_from)
                    to_val = int(range_to)
                    if current < from_val or current > to_val:
                        errors.append(
                            f"Consecutivo {current} fuera de rango "
                            f"[{from_val}-{to_val}]"
                        )
            except (ValueError, AttributeError):
                pass

        return errors


def validate_invoice(data: Any, config: Any) -> None:
    """Validar factura y lanzar excepcion si hay errores."""
    validator = InvoiceValidator()
    errors = validator.validate(data, config)
    if errors:
        raise ValidationError("Datos de factura invalidos", errors=errors)


def validate_before_build(
    data: Any,
    config: Any,
    doc_type: str = "factura"
) -> None:
    """Validar antes de construir XML."""
    validator = InvoiceValidator()
    errors = validator.validate(data, config)
    if errors:
        raise ValidationError(f"Datos de {doc_type} invalidos", errors=errors)


# =============================================================================
# VALIDACIONES DE PRODUCCION
# =============================================================================

def validate_resolution_dates(
    start_date: str,
    end_date: str,
    issue_date: str,
    field_name: str = "Resolucion"
) -> List[str]:
    """
    Validar que la fecha de emision este dentro del periodo de resolucion.

    Args:
        start_date: Fecha inicio de resolucion (YYYY-MM-DD)
        end_date: Fecha fin de resolucion (YYYY-MM-DD)
        issue_date: Fecha de emision del documento (YYYY-MM-DD)
        field_name: Nombre del campo para mensajes de error

    Returns:
        Lista de errores (vacia si todo esta correcto)
    """
    errors = []

    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        issue = datetime.strptime(issue_date, '%Y-%m-%d')

        if issue < start:
            errors.append(
                f"Fecha emision {issue_date} anterior a inicio de "
                f"{field_name.lower()} {start_date}"
            )
        if issue > end:
            errors.append(
                f"Fecha emision {issue_date} posterior a fin de "
                f"{field_name.lower()} {end_date}"
            )

    except ValueError as e:
        errors.append(f"Error en formato de fechas: {e}")

    return errors


# Patron para validar CUFE/CUDE (96 caracteres hexadecimales)
CUFE_PATTERN = re.compile(r'^[0-9a-f]{96}$', re.IGNORECASE)


def validate_cufe_format(cufe: str, field_name: str = "CUFE") -> List[str]:
    """
    Validar formato de CUFE/CUDE (96 caracteres hexadecimales).

    Args:
        cufe: Codigo CUFE o CUDE a validar
        field_name: Nombre del campo para mensajes de error

    Returns:
        Lista de errores (vacia si el formato es correcto)
    """
    errors = []

    if not cufe:
        errors.append(f"{field_name} es requerido")
        return errors

    if len(cufe) != 96:
        errors.append(
            f"{field_name} debe tener 96 caracteres (tiene {len(cufe)})"
        )

    if not CUFE_PATTERN.match(cufe):
        errors.append(f"{field_name} debe ser hexadecimal")

    return errors


def validate_consecutive_in_range(
    consecutive: int,
    range_from: int,
    range_to: int,
    prefix: str = ""
) -> List[str]:
    """
    Validar que el consecutivo este dentro del rango autorizado.

    Args:
        consecutive: Numero consecutivo actual
        range_from: Inicio del rango autorizado
        range_to: Fin del rango autorizado
        prefix: Prefijo del documento (opcional)

    Returns:
        Lista de errores (vacia si esta en rango)
    """
    errors = []

    if consecutive < range_from:
        errors.append(
            f"Consecutivo {prefix}{consecutive} menor que "
            f"rango minimo ({range_from})"
        )

    if consecutive > range_to:
        errors.append(
            f"Consecutivo {prefix}{consecutive} mayor que "
            f"rango maximo ({range_to})"
        )

    return errors


def validate_totals(
    line_extension: float,
    tax_exclusive: float,
    tax_inclusive: float,
    tax_amount: float,
    payable_amount: float,
    tolerance: float = 2.0
) -> List[str]:
    """
    Validar que los totales cuadren (DIAN permite tolerancia de ±2.00).

    Args:
        line_extension: Suma de subtotales de lineas
        tax_exclusive: Total sin impuestos
        tax_inclusive: Total con impuestos
        tax_amount: Suma de impuestos
        payable_amount: Total a pagar
        tolerance: Tolerancia permitida (default: 2.00)

    Returns:
        Lista de errores de validacion
    """
    errors = []

    # tax_inclusive = tax_exclusive + tax_amount
    expected_inclusive = tax_exclusive + tax_amount
    diff = abs(tax_inclusive - expected_inclusive)
    if diff > tolerance:
        errors.append(
            f"TaxInclusiveAmount ({tax_inclusive:.2f}) no cuadra con "
            f"TaxExclusiveAmount ({tax_exclusive:.2f}) + "
            f"TaxAmount ({tax_amount:.2f}). Diferencia: {diff:.2f}"
        )

    # payable_amount == tax_inclusive (normalmente)
    diff_payable = abs(payable_amount - tax_inclusive)
    if diff_payable > tolerance:
        errors.append(
            f"PayableAmount ({payable_amount:.2f}) no cuadra con "
            f"TaxInclusiveAmount ({tax_inclusive:.2f}). "
            f"Diferencia: {diff_payable:.2f}"
        )

    return errors


def validate_credit_note_reference(
    invoice_number: str,
    invoice_cufe: str,
    invoice_date: str,
    response_code: str
) -> List[str]:
    """
    Validar referencia de nota credito.

    Args:
        invoice_number: Numero de factura referenciada
        invoice_cufe: CUFE de la factura referenciada
        invoice_date: Fecha de la factura referenciada
        response_code: Codigo de respuesta/motivo

    Returns:
        Lista de errores de validacion
    """
    errors = []

    errors.extend(validate_not_empty(invoice_number, "Numero factura referenciada"))
    errors.extend(validate_cufe_format(invoice_cufe, "CUFE factura referenciada"))
    errors.extend(validate_date(invoice_date, "Fecha factura referenciada"))

    valid_codes = {'1', '2', '3', '4', '5'}
    if response_code not in valid_codes:
        errors.append(
            f"Codigo de respuesta invalido: {response_code}. "
            f"Debe ser uno de: {', '.join(sorted(valid_codes))}"
        )

    return errors


def validate_debit_note_reference(
    invoice_number: str,
    invoice_cufe: str,
    invoice_date: str,
    response_code: str
) -> List[str]:
    """
    Validar referencia de nota debito.

    Args:
        invoice_number: Numero de factura referenciada
        invoice_cufe: CUFE de la factura referenciada
        invoice_date: Fecha de la factura referenciada
        response_code: Codigo de respuesta/motivo

    Returns:
        Lista de errores de validacion
    """
    errors = []

    errors.extend(validate_not_empty(invoice_number, "Numero factura referenciada"))
    errors.extend(validate_cufe_format(invoice_cufe, "CUFE factura referenciada"))
    errors.extend(validate_date(invoice_date, "Fecha factura referenciada"))

    valid_codes = {'1', '2', '3', '4'}
    if response_code not in valid_codes:
        errors.append(
            f"Codigo de respuesta invalido: {response_code}. "
            f"Debe ser uno de: {', '.join(sorted(valid_codes))}"
        )

    return errors


def validate_export_invoice(
    destination_country: str,
    currency: str,
    valid_currencies: List[str] = None
) -> List[str]:
    """
    Validar factura de exportacion.

    Args:
        destination_country: Pais de destino
        currency: Moneda del documento
        valid_currencies: Lista de monedas validas

    Returns:
        Lista de errores de validacion
    """
    errors = []

    if valid_currencies is None:
        valid_currencies = ['COP', 'USD', 'EUR', 'GBP', 'MXN', 'BRL', 'ARS',
                            'CLP', 'PEN', 'JPY', 'CHF', 'CAD']

    # Pais destino NO puede ser Colombia
    if destination_country and destination_country.upper() == 'CO':
        errors.append(
            "Factura exportacion requiere pais destino diferente a Colombia"
        )

    # Moneda valida
    if currency and currency.upper() not in valid_currencies:
        errors.append(f"Moneda no valida para exportacion: {currency}")

    return errors


def validate_pos_limits(
    total: float,
    uvt_limit: int,
    uvt_value: float
) -> List[str]:
    """
    Validar limite de UVT para documento POS.

    Args:
        total: Total del documento
        uvt_limit: Limite en UVT (normalmente 5)
        uvt_value: Valor del UVT para el ano

    Returns:
        Lista de errores de validacion
    """
    errors = []

    max_value = uvt_limit * uvt_value
    if total > max_value:
        errors.append(
            f"Total ${total:,.2f} excede limite POS de {uvt_limit} UVT "
            f"(${max_value:,.2f})"
        )

    return errors


def calculate_remaining_in_range(
    current: int,
    range_to: int
) -> int:
    """
    Calcular consecutivos restantes en el rango.

    Args:
        current: Consecutivo actual
        range_to: Fin del rango autorizado

    Returns:
        Cantidad de consecutivos restantes
    """
    return max(0, range_to - current)


def is_resolution_expiring_soon(
    end_date: str,
    days_warning: int = 30
) -> bool:
    """
    Verificar si la resolucion esta proxima a vencer.

    Args:
        end_date: Fecha de fin de resolucion (YYYY-MM-DD)
        days_warning: Dias de anticipacion para advertencia

    Returns:
        True si la resolucion vence en menos de days_warning dias
    """
    try:
        end = datetime.strptime(end_date, '%Y-%m-%d')
        today = datetime.now()
        remaining = (end - today).days
        return remaining <= days_warning
    except ValueError:
        return False


class ProductionValidator:
    """
    Validador para ambiente de produccion DIAN.

    Agrupa todas las validaciones necesarias antes de enviar
    un documento a produccion.
    """

    def __init__(self, uvt_value: float = 47065.0):
        """
        Inicializar validador de produccion.

        Args:
            uvt_value: Valor UVT del ano actual
        """
        self.uvt_value = uvt_value

    def validate_invoice_for_production(
        self,
        data: Any,
        config: Any
    ) -> List[str]:
        """
        Validar factura completa para produccion.

        Args:
            data: Datos de la factura
            config: Configuracion de facturacion

        Returns:
            Lista de todos los errores encontrados
        """
        errors = []

        # Validacion basica
        validator = InvoiceValidator()
        errors.extend(validator.validate(data, config))

        # Validar fechas de resolucion
        start_date = getattr(config, 'resolution_date', None)
        end_date = getattr(config, 'resolution_end_date', None)
        issue_date = getattr(data, 'issue_date', None)

        if start_date and end_date and issue_date:
            errors.extend(validate_resolution_dates(
                start_date, end_date, issue_date
            ))

        return errors

    def validate_credit_note_for_production(
        self,
        data: Any,
        reference_number: str,
        reference_cufe: str,
        reference_date: str,
        response_code: str
    ) -> List[str]:
        """
        Validar nota credito para produccion.

        Args:
            data: Datos de la nota credito
            reference_number: Numero de factura referenciada
            reference_cufe: CUFE de factura referenciada
            reference_date: Fecha de factura referenciada
            response_code: Codigo de respuesta

        Returns:
            Lista de errores de validacion
        """
        errors = []

        # Validar referencia
        errors.extend(validate_credit_note_reference(
            reference_number,
            reference_cufe,
            reference_date,
            response_code
        ))

        return errors

    def validate_pos_document(
        self,
        total: float,
        uvt_limit: int = 5
    ) -> List[str]:
        """
        Validar documento POS.

        Args:
            total: Total del documento
            uvt_limit: Limite en UVT (default: 5)

        Returns:
            Lista de errores de validacion
        """
        return validate_pos_limits(total, uvt_limit, self.uvt_value)
