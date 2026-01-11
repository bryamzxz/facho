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
