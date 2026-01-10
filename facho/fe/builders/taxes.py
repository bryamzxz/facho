# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Sistema de impuestos flexible para facturacion electronica DIAN Colombia.

Soporta todos los tipos de impuesto definidos por DIAN:
- IVA (01): Impuesto al Valor Agregado
- IC (02): Impuesto al Consumo
- ICA (03): Impuesto de Industria y Comercio
- INC (04): Impuesto Nacional al Consumo
- ReteIVA (05): Retencion de IVA
- ReteFte (06): Retencion en la Fuente
- ReteICA (07): Retencion de ICA
- Y otros impuestos adicionales (22-36)
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from decimal import Decimal, ROUND_DOWN


# =============================================================================
# CONSTANTES DE IMPUESTOS DIAN
# =============================================================================

# Codigos de impuesto DIAN segun Anexo Tecnico
TAX_CODES = {
    # Impuestos principales
    'IVA': '01',        # Impuesto al Valor Agregado
    'IC': '02',         # Impuesto al Consumo
    'ICA': '03',        # Impuesto de Industria y Comercio
    'INC': '04',        # Impuesto Nacional al Consumo

    # Retenciones
    'ReteIVA': '05',    # Retencion de IVA
    'ReteFte': '06',    # Retencion en la Fuente
    'ReteICA': '07',    # Retencion de ICA

    # Impuestos adicionales
    'FtoHorticultura': '20',     # Fondo de Fomento Horticultura
    'Timbre': '21',              # Timbre
    'IVA_e': '22',               # IVA e
    'IC_e': '23',                # IC e
    'INC_e': '24',               # INC e
    'ReteIVA_e': '25',           # ReteIVA e
    'ReteFte_e': '26',           # ReteFte e
    'ReteICA_e': '27',           # ReteICA e
    'IC_Porcentual': '30',       # IC Porcentual
    'FtoCacao': '32',            # Fondo Estabilizacion Cacao
    'FtoPalma': '33',            # Fondo Estabilizacion Palma
    'Bolsas': '34',              # Impuesto Nacional Bolsas
    'Combustibles': '35',        # Impuesto Nacional Combustibles
    'CarbonoCO2': '36',          # Impuesto al Carbono CO2

    # Impuestos especiales Bogota
    'SobreTasaBomberil': 'ZZ',   # Sobretasa Bomberil
}

# Nombres de impuesto por codigo
TAX_NAMES = {
    '01': 'IVA',
    '02': 'IC',
    '03': 'ICA',
    '04': 'INC',
    '05': 'ReteIVA',
    '06': 'ReteFte',
    '07': 'ReteICA',
    '20': 'FtoHorticultura',
    '21': 'Timbre',
    '22': 'IVA e',
    '23': 'IC e',
    '24': 'INC e',
    '25': 'ReteIVA e',
    '26': 'ReteFte e',
    '27': 'ReteICA e',
    '30': 'IC Porcentual',
    '32': 'FtoCacao',
    '33': 'FtoPalma',
    '34': 'Bolsas',
    '35': 'Combustibles',
    '36': 'CarbonoCO2',
    'ZZ': 'SobreTasaBomberil',
}

# Codigos de retencion (van en WithholdingTaxTotal)
WITHHOLDING_TAX_CODES = {'05', '06', '07', '25', '26', '27'}

# Tasas de IVA comunes en Colombia
IVA_RATES = {
    'general': 19.0,
    'reducida': 5.0,
    'excluido': 0.0,
    'exento': 0.0,
}

# Tasas de retencion comunes
RETENTION_RATES = {
    'rete_iva': 15.0,       # Retencion de IVA (15% del IVA)
    'rete_fte_servicios': 11.0,  # Retencion por servicios
    'rete_fte_compras': 2.5,     # Retencion por compras
    'rete_fte_honorarios': 11.0, # Retencion por honorarios
    'rete_ica': 0.0,        # Varia por municipio
}


# =============================================================================
# UTILIDADES DE TRUNCAMIENTO
# =============================================================================

def truncar(valor: float, decimales: int = 2) -> float:
    """
    Truncar valor a N decimales (DIAN no redondea, trunca).

    Args:
        valor: Valor a truncar
        decimales: Numero de decimales (default 2)

    Returns:
        Valor truncado

    Example:
        >>> truncar(123.456789, 2)
        123.45
        >>> truncar(99.999, 2)
        99.99
    """
    factor = 10 ** decimales
    return math.trunc(valor * factor) / factor


def truncar_decimal(valor: float, decimales: int = 2) -> Decimal:
    """
    Truncar valor usando Decimal para precision.

    Args:
        valor: Valor a truncar
        decimales: Numero de decimales

    Returns:
        Valor truncado como Decimal
    """
    d = Decimal(str(valor))
    quantize_str = '0.' + '0' * decimales
    return d.quantize(Decimal(quantize_str), rounding=ROUND_DOWN)


def formato_dinero(valor: float, decimales: int = 2) -> str:
    """
    Formato DIAN para valores monetarios.

    Args:
        valor: Valor a formatear
        decimales: Numero de decimales (default 2)

    Returns:
        String formateado con decimales truncados

    Example:
        >>> formato_dinero(123.456)
        '123.45'
    """
    return f"{truncar(valor, decimales):.{decimales}f}"


# =============================================================================
# DATACLASS TAX
# =============================================================================

@dataclass
class Tax:
    """
    Representa un impuesto o retencion.

    Soporta todos los tipos de impuesto DIAN incluyendo:
    - Impuestos regulares (IVA, IC, ICA, INC)
    - Retenciones (ReteIVA, ReteFte, ReteICA)
    - Impuestos especiales (Bolsas, Combustibles, etc.)

    Attributes:
        code: Codigo DIAN del impuesto ('01', '03', '05', etc.)
        name: Nombre del impuesto (se autocompleta si no se proporciona)
        percent: Porcentaje del impuesto (ej: 19.0 para IVA 19%)
        amount: Monto del impuesto (calculado o fijo)
        taxable_amount: Base gravable sobre la que se calcula
        is_withholding: True si es retencion (se suma en WithholdingTaxTotal)
        unit_amount: Monto por unidad (para impuestos por unidad como IC)
        per_unit_code: Codigo de unidad (ej: '94' para unidad)

    Example:
        # IVA 19%
        Tax(code='01', percent=19.0, taxable_amount=100000)

        # IVA 5%
        Tax(code='01', percent=5.0, taxable_amount=50000)

        # ICA (varia por ciudad)
        Tax(code='03', percent=0.966, taxable_amount=100000)

        # Retencion en la fuente
        Tax(code='06', percent=11.0, taxable_amount=100000, is_withholding=True)

        # Impuesto al consumo por unidad
        Tax(code='02', unit_amount=2000, taxable_amount=10000, amount=2000)
    """
    code: str
    percent: float = 0.0
    taxable_amount: float = 0.0
    amount: float = None  # Si es None, se calcula automaticamente
    name: str = None      # Si es None, se obtiene de TAX_NAMES
    is_withholding: bool = None  # Si es None, se determina por codigo
    unit_amount: float = None    # Para impuestos por unidad (IC)
    per_unit_code: str = None    # Codigo de unidad

    def __post_init__(self):
        """Inicializar valores por defecto."""
        # Obtener nombre si no se proporciono
        if self.name is None:
            self.name = TAX_NAMES.get(self.code, f'Impuesto {self.code}')

        # Determinar si es retencion por codigo
        if self.is_withholding is None:
            self.is_withholding = self.code in WITHHOLDING_TAX_CODES

        # Calcular monto si no se proporciono
        if self.amount is None:
            if self.unit_amount is not None:
                # Impuesto por unidad
                self.amount = self.unit_amount
            else:
                # Impuesto porcentual
                self.amount = truncar(self.taxable_amount * (self.percent / 100))

    @classmethod
    def iva(cls, percent: float, taxable_amount: float) -> 'Tax':
        """
        Crear impuesto IVA.

        Args:
            percent: Porcentaje de IVA (19, 5, 0)
            taxable_amount: Base gravable

        Returns:
            Instancia de Tax para IVA
        """
        return cls(
            code='01',
            name='IVA',
            percent=percent,
            taxable_amount=taxable_amount,
            is_withholding=False
        )

    @classmethod
    def iva_19(cls, taxable_amount: float) -> 'Tax':
        """Crear IVA al 19%."""
        return cls.iva(19.0, taxable_amount)

    @classmethod
    def iva_5(cls, taxable_amount: float) -> 'Tax':
        """Crear IVA al 5%."""
        return cls.iva(5.0, taxable_amount)

    @classmethod
    def iva_0(cls, taxable_amount: float) -> 'Tax':
        """Crear IVA al 0% (exento/excluido)."""
        return cls.iva(0.0, taxable_amount)

    @classmethod
    def inc(cls, percent: float, taxable_amount: float) -> 'Tax':
        """
        Crear Impuesto Nacional al Consumo (INC).

        Args:
            percent: Porcentaje de INC (4, 8, 16)
            taxable_amount: Base gravable
        """
        return cls(
            code='04',
            name='INC',
            percent=percent,
            taxable_amount=taxable_amount,
            is_withholding=False
        )

    @classmethod
    def ic(cls, amount: float, taxable_amount: float = 0.0) -> 'Tax':
        """
        Crear Impuesto al Consumo (IC) - monto fijo por unidad.

        Args:
            amount: Monto del impuesto
            taxable_amount: Base gravable (opcional)
        """
        return cls(
            code='02',
            name='IC',
            percent=0.0,
            amount=amount,
            taxable_amount=taxable_amount,
            unit_amount=amount,
            is_withholding=False
        )

    @classmethod
    def ica(cls, percent: float, taxable_amount: float) -> 'Tax':
        """
        Crear Impuesto de Industria y Comercio (ICA).

        Args:
            percent: Porcentaje de ICA (varia por municipio, ej: 0.966)
            taxable_amount: Base gravable
        """
        return cls(
            code='03',
            name='ICA',
            percent=percent,
            taxable_amount=taxable_amount,
            is_withholding=False
        )

    @classmethod
    def rete_iva(cls, iva_amount: float, percent: float = 15.0) -> 'Tax':
        """
        Crear Retencion de IVA.

        Args:
            iva_amount: Monto del IVA sobre el que se retiene
            percent: Porcentaje de retencion (default 15%)
        """
        return cls(
            code='05',
            name='ReteIVA',
            percent=percent,
            taxable_amount=iva_amount,
            is_withholding=True
        )

    @classmethod
    def rete_fte(cls, percent: float, taxable_amount: float) -> 'Tax':
        """
        Crear Retencion en la Fuente.

        Args:
            percent: Porcentaje de retencion
            taxable_amount: Base de retencion
        """
        return cls(
            code='06',
            name='ReteFte',
            percent=percent,
            taxable_amount=taxable_amount,
            is_withholding=True
        )

    @classmethod
    def rete_ica(cls, percent: float, taxable_amount: float) -> 'Tax':
        """
        Crear Retencion de ICA.

        Args:
            percent: Porcentaje de retencion ICA
            taxable_amount: Base de retencion
        """
        return cls(
            code='07',
            name='ReteICA',
            percent=percent,
            taxable_amount=taxable_amount,
            is_withholding=True
        )


@dataclass
class TaxTotal:
    """
    Representa el total de un tipo de impuesto.

    Agrupa todos los impuestos del mismo codigo para el TaxTotal del documento.

    Attributes:
        code: Codigo del impuesto
        name: Nombre del impuesto
        total_amount: Suma total del impuesto
        total_taxable_amount: Suma total de bases gravables
        subtotals: Lista de Tax individuales que componen el total
    """
    code: str
    name: str
    total_amount: float = 0.0
    total_taxable_amount: float = 0.0
    subtotals: List[Tax] = field(default_factory=list)
    is_withholding: bool = False

    def add_tax(self, tax: Tax):
        """Agregar un impuesto al total."""
        self.subtotals.append(tax)
        self.total_amount = truncar(self.total_amount + tax.amount)
        self.total_taxable_amount = truncar(self.total_taxable_amount + tax.taxable_amount)
        self.is_withholding = tax.is_withholding


def agrupar_impuestos(taxes: List[Tax]) -> Dict[str, TaxTotal]:
    """
    Agrupar impuestos por codigo.

    Args:
        taxes: Lista de impuestos a agrupar

    Returns:
        Diccionario con codigo -> TaxTotal
    """
    totales: Dict[str, TaxTotal] = {}

    for tax in taxes:
        if tax.code not in totales:
            totales[tax.code] = TaxTotal(
                code=tax.code,
                name=tax.name,
                is_withholding=tax.is_withholding
            )
        totales[tax.code].add_tax(tax)

    return totales


def separar_impuestos_retenciones(taxes: List[Tax]) -> tuple:
    """
    Separar impuestos regulares de retenciones.

    Args:
        taxes: Lista de todos los impuestos

    Returns:
        Tuple (impuestos_regulares, retenciones)
    """
    impuestos = [t for t in taxes if not t.is_withholding]
    retenciones = [t for t in taxes if t.is_withholding]
    return impuestos, retenciones


def calcular_totales_impuestos(taxes: List[Tax]) -> Dict[str, float]:
    """
    Calcular totales por codigo de impuesto.

    Util para calcular CUFE/CUDE.

    Args:
        taxes: Lista de impuestos

    Returns:
        Diccionario con codigo -> monto total

    Example:
        >>> taxes = [Tax.iva_19(100000), Tax.ica(0.966, 100000)]
        >>> calcular_totales_impuestos(taxes)
        {'01': 19000.0, '03': 966.0}
    """
    totales: Dict[str, float] = {}

    for tax in taxes:
        if tax.code not in totales:
            totales[tax.code] = 0.0
        totales[tax.code] = truncar(totales[tax.code] + tax.amount)

    return totales
