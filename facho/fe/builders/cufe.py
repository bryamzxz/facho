# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Calculador de CUFE/CUDE/CUDS segun Anexo Tecnico DIAN v1.9.

CUFE (Codigo Unico de Factura Electronica):
    Para facturas de venta. Usa clave tecnica.

CUDE (Codigo Unico de Documento Electronico):
    Para notas credito, notas debito y documentos POS. Usa SoftwarePIN.

CUDS (Codigo Unico de Documento Soporte):
    Para documentos soporte. Usa SoftwarePIN.

Formula general:
    SHA384(NumDoc + FecDoc + HoraDoc + ValorBruto + 01 + ValorIVA +
           04 + ValorINC + 03 + ValorICA + ValorTotal + NitEmisor +
           NumAdquiriente + ClaveTecnica/PIN + TipoAmbiente)
"""

import hashlib
from dataclasses import dataclass
from typing import Dict, Optional

from .taxes import truncar


@dataclass
class CufeInput:
    """
    Datos de entrada para calcular CUFE/CUDE/CUDS.

    Attributes:
        number: Numero del documento con prefijo (ej: 'SETP990000001')
        issue_date: Fecha de emision (YYYY-MM-DD)
        issue_time: Hora de emision (HH:MM:SS-05:00)
        subtotal: Valor subtotal (LineExtensionAmount)
        iva_amount: Valor IVA - codigo 01 (default 0.0)
        inc_amount: Valor INC - codigo 04 (default 0.0)
        ica_amount: Valor ICA - codigo 03 (default 0.0)
        total: Valor total (PayableAmount)
        supplier_nit: NIT del emisor
        customer_nit: NIT/documento del adquiriente
        technical_key: Clave tecnica (CUFE) o PIN (CUDE/CUDS)
        environment: Tipo de ambiente ('1'=Produccion, '2'=Pruebas)
    """
    number: str
    issue_date: str
    issue_time: str
    subtotal: float
    total: float
    supplier_nit: str
    customer_nit: str
    technical_key: str
    environment: str = '2'
    iva_amount: float = 0.0
    inc_amount: float = 0.0
    ica_amount: float = 0.0


def format_amount(value: float, decimals: int = 2) -> str:
    """
    Formatear valor monetario para CUFE (2 decimales truncados).

    IMPORTANTE: DIAN trunca, no redondea.

    Args:
        value: Valor a formatear
        decimals: Numero de decimales (default 2)

    Returns:
        String formateado con decimales truncados

    Example:
        >>> format_amount(123.456)
        '123.45'
        >>> format_amount(99.999)
        '99.99'
    """
    truncated = truncar(value, decimals)
    return f"{truncated:.{decimals}f}"


def build_cufe_string(data: CufeInput) -> str:
    """
    Construir cadena para calculo de CUFE/CUDE.

    Cadena segun Anexo Tecnico DIAN:
    NumDoc + FecDoc + HoraDoc + ValorBruto + 01 + ValorIVA +
    04 + ValorINC + 03 + ValorICA + ValorTotal + NitEmisor +
    NumAdquiriente + ClaveTecnica + TipoAmbiente

    Args:
        data: Datos del documento

    Returns:
        Cadena concatenada para hash
    """
    return (
        f"{data.number}"
        f"{data.issue_date}"
        f"{data.issue_time}"
        f"{format_amount(data.subtotal)}"
        f"01"
        f"{format_amount(data.iva_amount)}"
        f"04"
        f"{format_amount(data.inc_amount)}"
        f"03"
        f"{format_amount(data.ica_amount)}"
        f"{format_amount(data.total)}"
        f"{data.supplier_nit}"
        f"{data.customer_nit}"
        f"{data.technical_key}"
        f"{data.environment}"
    )


def calculate_cufe(data: CufeInput) -> str:
    """
    Calcular CUFE para facturas.

    El CUFE usa la clave tecnica proporcionada por DIAN para
    el set de resolucion de numeracion.

    Args:
        data: Datos de la factura

    Returns:
        CUFE de 96 caracteres hexadecimales (SHA-384)

    Example:
        >>> data = CufeInput(
        ...     number='SETP990000001',
        ...     issue_date='2026-01-18',
        ...     issue_time='10:30:00-05:00',
        ...     subtotal=100000.00,
        ...     iva_amount=19000.00,
        ...     total=119000.00,
        ...     supplier_nit='1001186599',
        ...     customer_nit='222222222222',
        ...     technical_key='clave_tecnica_dian',
        ...     environment='2'
        ... )
        >>> cufe = calculate_cufe(data)
        >>> len(cufe)
        96
    """
    cadena = build_cufe_string(data)
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def calculate_cude(data: CufeInput, software_pin: str = None) -> str:
    """
    Calcular CUDE para notas credito/debito y documentos POS.

    El CUDE usa el PIN del software en lugar de la clave tecnica.

    Args:
        data: Datos del documento
        software_pin: PIN del software DIAN (si no se incluye en data.technical_key)

    Returns:
        CUDE de 96 caracteres hexadecimales (SHA-384)

    Example:
        >>> data = CufeInput(
        ...     number='NC1',
        ...     issue_date='2026-01-18',
        ...     issue_time='10:30:00-05:00',
        ...     subtotal=50000.00,
        ...     iva_amount=9500.00,
        ...     total=59500.00,
        ...     supplier_nit='1001186599',
        ...     customer_nit='222222222222',
        ...     technical_key='software_pin',
        ...     environment='2'
        ... )
        >>> cude = calculate_cude(data)
        >>> len(cude)
        96
    """
    # Si se proporciona software_pin, usarlo; sino usar technical_key
    if software_pin:
        data_copy = CufeInput(
            number=data.number,
            issue_date=data.issue_date,
            issue_time=data.issue_time,
            subtotal=data.subtotal,
            iva_amount=data.iva_amount,
            inc_amount=data.inc_amount,
            ica_amount=data.ica_amount,
            total=data.total,
            supplier_nit=data.supplier_nit,
            customer_nit=data.customer_nit,
            technical_key=software_pin,
            environment=data.environment,
        )
        cadena = build_cufe_string(data_copy)
    else:
        cadena = build_cufe_string(data)

    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def calculate_cuds(data: CufeInput, software_pin: str = None) -> str:
    """
    Calcular CUDS para documentos soporte.

    El CUDS usa el PIN del software igual que el CUDE.

    Args:
        data: Datos del documento soporte
        software_pin: PIN del software DIAN

    Returns:
        CUDS de 96 caracteres hexadecimales (SHA-384)
    """
    return calculate_cude(data, software_pin)


def calculate_cufe_from_taxes(
    number: str,
    issue_date: str,
    issue_time: str,
    subtotal: float,
    taxes: Dict[str, float],
    total: float,
    supplier_nit: str,
    customer_nit: str,
    technical_key: str,
    environment: str = '2'
) -> str:
    """
    Calcular CUFE con diccionario de impuestos.

    Util cuando se tienen los impuestos ya agrupados por codigo.

    Args:
        number: Numero del documento
        issue_date: Fecha de emision (YYYY-MM-DD)
        issue_time: Hora de emision (HH:MM:SS-05:00)
        subtotal: Valor subtotal
        taxes: Diccionario con codigo de impuesto -> monto
               Ej: {'01': 19000.0, '03': 966.0, '04': 0.0}
        total: Valor total
        supplier_nit: NIT del emisor
        customer_nit: NIT del adquiriente
        technical_key: Clave tecnica DIAN
        environment: '1' produccion, '2' pruebas

    Returns:
        CUFE en formato SHA-384 hexadecimal
    """
    data = CufeInput(
        number=number,
        issue_date=issue_date,
        issue_time=issue_time,
        subtotal=subtotal,
        iva_amount=taxes.get('01', 0.0),
        inc_amount=taxes.get('04', 0.0),
        ica_amount=taxes.get('03', 0.0),
        total=total,
        supplier_nit=supplier_nit,
        customer_nit=customer_nit,
        technical_key=technical_key,
        environment=environment,
    )
    return calculate_cufe(data)


def calculate_cude_from_taxes(
    number: str,
    issue_date: str,
    issue_time: str,
    subtotal: float,
    taxes: Dict[str, float],
    total: float,
    supplier_nit: str,
    customer_nit: str,
    software_pin: str,
    environment: str = '2'
) -> str:
    """
    Calcular CUDE con diccionario de impuestos.

    Args:
        number: Numero del documento
        issue_date: Fecha de emision (YYYY-MM-DD)
        issue_time: Hora de emision (HH:MM:SS-05:00)
        subtotal: Valor subtotal
        taxes: Diccionario con codigo de impuesto -> monto
        total: Valor total
        supplier_nit: NIT del emisor
        customer_nit: NIT del adquiriente
        software_pin: PIN del software DIAN
        environment: '1' produccion, '2' pruebas

    Returns:
        CUDE en formato SHA-384 hexadecimal
    """
    data = CufeInput(
        number=number,
        issue_date=issue_date,
        issue_time=issue_time,
        subtotal=subtotal,
        iva_amount=taxes.get('01', 0.0),
        inc_amount=taxes.get('04', 0.0),
        ica_amount=taxes.get('03', 0.0),
        total=total,
        supplier_nit=supplier_nit,
        customer_nit=customer_nit,
        technical_key=software_pin,
        environment=environment,
    )
    return calculate_cude(data)


def calculate_software_security_code(
    software_id: str,
    software_pin: str,
    doc_number: str
) -> str:
    """
    Calcular SoftwareSecurityCode.

    SoftwareSecurityCode = SHA384(SoftwareID + PIN + NumeroDocumento)

    Este codigo se incluye en los documentos electronicos para
    verificar la autenticidad del software emisor.

    Args:
        software_id: ID del software DIAN (UUID)
        software_pin: PIN del software
        doc_number: Numero del documento

    Returns:
        Hash SHA-384 hexadecimal (96 caracteres)
    """
    cadena = f"{software_id}{software_pin}{doc_number}"
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def verify_cufe(cufe: str, data: CufeInput) -> bool:
    """
    Verificar si un CUFE es correcto.

    Args:
        cufe: CUFE a verificar
        data: Datos originales del documento

    Returns:
        True si el CUFE coincide con los datos
    """
    calculated = calculate_cufe(data)
    return cufe.lower() == calculated.lower()


def verify_cude(cude: str, data: CufeInput, software_pin: str = None) -> bool:
    """
    Verificar si un CUDE es correcto.

    Args:
        cude: CUDE a verificar
        data: Datos originales del documento
        software_pin: PIN del software (opcional)

    Returns:
        True si el CUDE coincide con los datos
    """
    calculated = calculate_cude(data, software_pin)
    return cude.lower() == calculated.lower()


def get_uuid_type(doc_type_code: str) -> str:
    """
    Obtener el tipo de UUID segun el tipo de documento.

    Args:
        doc_type_code: Codigo del tipo de documento ('01', '91', '92', etc.)

    Returns:
        Tipo de UUID ('CUFE-SHA384', 'CUDE-SHA384', 'CUDS-SHA384')
    """
    uuid_types = {
        '01': 'CUFE-SHA384',  # Factura
        '02': 'CUFE-SHA384',  # Exportacion
        '03': 'CUDE-SHA384',  # POS
        '04': 'CUFE-SHA384',  # Contingencia
        '05': 'CUDS-SHA384',  # Documento soporte
        '91': 'CUDE-SHA384',  # Nota credito
        '92': 'CUDE-SHA384',  # Nota debito
        '95': 'CUDS-SHA384',  # Nota ajuste doc soporte
    }
    return uuid_types.get(doc_type_code, 'CUFE-SHA384')


def calculate_uuid_by_doc_type(
    data: CufeInput,
    doc_type_code: str,
    software_pin: str = None
) -> str:
    """
    Calcular UUID segun el tipo de documento.

    Automaticamente selecciona si usar CUFE, CUDE o CUDS.

    Args:
        data: Datos del documento
        doc_type_code: Codigo del tipo de documento
        software_pin: PIN del software (requerido para CUDE/CUDS)

    Returns:
        UUID del documento (96 caracteres hexadecimales)
    """
    uuid_type = get_uuid_type(doc_type_code)

    if uuid_type == 'CUFE-SHA384':
        return calculate_cufe(data)
    elif uuid_type in ('CUDE-SHA384', 'CUDS-SHA384'):
        return calculate_cude(data, software_pin)
    else:
        return calculate_cufe(data)
