# This file is part of dian_fe.
"""
Utilidades para calculos DIAN.
Incluye CUFE, CUDE, DV y funciones de hash.
"""

import base64
import hashlib


def calcular_dv(nit: str) -> int:
    """
    Calcular digito de verificacion DIAN.

    Args:
        nit: Numero de identificacion tributaria

    Returns:
        Digito de verificacion (0-9)
    """
    nit = ''.join(filter(str.isdigit, str(nit)))
    primos = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
    nit = nit.zfill(15)
    suma = sum(int(nit[i]) * primos[i] for i in range(15))
    resto = suma % 11
    return 11 - resto if resto > 1 else resto


def calcular_cufe(
    numero: str,
    fecha_emision: str,
    hora_emision: str,
    subtotal: float,
    iva: float,
    total: float,
    nit_emisor: str,
    nit_adquiriente: str,
    clave_tecnica: str,
    tipo_ambiente: str = '2'
) -> str:
    """
    Calcular CUFE segun especificacion DIAN.

    El CUFE (Codigo Unico de Factura Electronica) se usa
    exclusivamente para facturas.

    Args:
        numero: Numero de factura
        fecha_emision: Fecha en formato YYYY-MM-DD
        hora_emision: Hora en formato HH:MM:SS-05:00
        subtotal: Valor subtotal
        iva: Valor IVA
        total: Valor total
        nit_emisor: NIT del emisor
        nit_adquiriente: NIT del adquiriente
        clave_tecnica: Clave tecnica DIAN
        tipo_ambiente: '1' produccion, '2' pruebas

    Returns:
        CUFE en formato SHA-384 hexadecimal (96 caracteres)
    """
    cadena = (
        f"{numero}{fecha_emision}{hora_emision}"
        f"{subtotal:.2f}01{iva:.2f}04{0:.2f}03{0:.2f}"
        f"{total:.2f}{nit_emisor}{nit_adquiriente}"
        f"{clave_tecnica}{tipo_ambiente}"
    )
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def calcular_cude(
    numero: str,
    fecha_emision: str,
    hora_emision: str,
    subtotal: float,
    iva: float,
    total: float,
    nit_emisor: str,
    nit_adquiriente: str,
    software_pin: str,
    tipo_ambiente: str = '2'
) -> str:
    """
    Calcular CUDE segun especificacion DIAN.

    El CUDE (Codigo Unico de Documento Electronico) se usa para
    notas credito y notas debito.

    IMPORTANTE: CUDE usa software_pin en lugar de clave_tecnica.

    Args:
        numero: Numero del documento
        fecha_emision: Fecha en formato YYYY-MM-DD
        hora_emision: Hora en formato HH:MM:SS-05:00
        subtotal: Valor subtotal
        iva: Valor IVA
        total: Valor total
        nit_emisor: NIT del emisor
        nit_adquiriente: NIT del adquiriente
        software_pin: PIN del software DIAN (NO clave tecnica)
        tipo_ambiente: '1' produccion, '2' pruebas

    Returns:
        CUDE en formato SHA-384 hexadecimal (96 caracteres)
    """
    cadena = (
        f"{numero}{fecha_emision}{hora_emision}"
        f"{subtotal:.2f}01{iva:.2f}04{0:.2f}03{0:.2f}"
        f"{total:.2f}{nit_emisor}{nit_adquiriente}"
        f"{software_pin}{tipo_ambiente}"
    )
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def calcular_software_security_code(
    software_id: str,
    pin: str,
    numero_factura: str
) -> str:
    """
    Calcular SoftwareSecurityCode.

    SHA384(SoftwareID + PIN + NumeroFactura)

    Args:
        software_id: ID del software DIAN
        pin: PIN del software
        numero_factura: Numero de la factura

    Returns:
        Hash SHA-384 hexadecimal
    """
    cadena = f"{software_id}{pin}{numero_factura}"
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def sha256_digest(data: bytes) -> str:
    """
    Calcular digest SHA-256 y retornar en base64.

    Args:
        data: Datos a hashear

    Returns:
        Digest en base64
    """
    return base64.b64encode(hashlib.sha256(data).digest()).decode('utf-8')


def sha384_digest(data: bytes) -> str:
    """
    Calcular digest SHA-384 y retornar en hexadecimal.

    Args:
        data: Datos a hashear

    Returns:
        Digest en hexadecimal
    """
    return hashlib.sha384(data).hexdigest()
