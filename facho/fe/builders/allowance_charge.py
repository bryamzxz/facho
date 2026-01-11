# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Descuentos y Cargos (AllowanceCharge) para documentos UBL 2.1.
"""

from dataclasses import dataclass
from typing import List, Tuple
from lxml import etree

from .constants import NS
from .taxes import truncar, formato_dinero


@dataclass
class AllowanceCharge:
    """
    Representa un descuento o cargo.

    Attributes:
        is_charge: True=cargo, False=descuento
        reason: Razon del descuento/cargo
        amount: Monto del descuento/cargo
        percent: Porcentaje (opcional)
        base_amount: Monto base sobre el que se calcula (opcional)
        allowance_charge_reason_code: Codigo de razon DIAN (opcional)
    """
    is_charge: bool
    reason: str
    amount: float = None
    percent: float = None
    base_amount: float = None
    allowance_charge_reason_code: str = None

    def __post_init__(self):
        """Calcular amount si se dio porcentaje y base."""
        if self.amount is None and self.percent is not None and self.base_amount is not None:
            self.amount = truncar(self.base_amount * (self.percent / 100))


# Codigos de razon de descuento DIAN
ALLOWANCE_REASON_CODES = {
    '00': 'Descuento no especificado',
    '01': 'Descuento por pronto pago',
    '02': 'Descuento por volumen',
    '03': 'Descuento especial',
    '04': 'Descuento comercial',
}

# Codigos de razon de cargo DIAN
CHARGE_REASON_CODES = {
    '00': 'Cargo no especificado',
    '01': 'Flete',
    '02': 'Empaque',
    '03': 'Seguros',
    '04': 'Otros cargos',
}


def create_discount(
    reason: str,
    amount: float = None,
    percent: float = None,
    base_amount: float = None,
    reason_code: str = None
) -> AllowanceCharge:
    """
    Crear un descuento.

    Args:
        reason: Razon del descuento
        amount: Monto del descuento (opcional si se da percent y base_amount)
        percent: Porcentaje de descuento (opcional)
        base_amount: Base sobre la cual se calcula el descuento (opcional)
        reason_code: Codigo de razon DIAN (opcional)

    Returns:
        AllowanceCharge configurado como descuento
    """
    return AllowanceCharge(
        is_charge=False,
        reason=reason,
        amount=amount,
        percent=percent,
        base_amount=base_amount,
        allowance_charge_reason_code=reason_code
    )


def create_charge(
    reason: str,
    amount: float = None,
    percent: float = None,
    base_amount: float = None,
    reason_code: str = None
) -> AllowanceCharge:
    """
    Crear un cargo.

    Args:
        reason: Razon del cargo
        amount: Monto del cargo (opcional si se da percent y base_amount)
        percent: Porcentaje del cargo (opcional)
        base_amount: Base sobre la cual se calcula el cargo (opcional)
        reason_code: Codigo de razon DIAN (opcional)

    Returns:
        AllowanceCharge configurado como cargo
    """
    return AllowanceCharge(
        is_charge=True,
        reason=reason,
        amount=amount,
        percent=percent,
        base_amount=base_amount,
        allowance_charge_reason_code=reason_code
    )


def add_allowance_charges_to_element(
    parent: etree._Element,
    allowance_charges: List[AllowanceCharge],
    currency: str = 'COP'
) -> None:
    """
    Agregar AllowanceCharge a un elemento XML.

    Args:
        parent: Elemento padre (Invoice, InvoiceLine, etc.)
        allowance_charges: Lista de descuentos/cargos
        currency: Codigo de moneda
    """
    for i, ac in enumerate(allowance_charges, 1):
        ac_el = etree.SubElement(parent, '{%s}AllowanceCharge' % NS['cac'])

        # ID
        etree.SubElement(ac_el, '{%s}ID' % NS['cbc']).text = str(i)

        # ChargeIndicator (true=cargo, false=descuento)
        etree.SubElement(
            ac_el, '{%s}ChargeIndicator' % NS['cbc']
        ).text = 'true' if ac.is_charge else 'false'

        # AllowanceChargeReasonCode (opcional)
        if ac.allowance_charge_reason_code:
            etree.SubElement(
                ac_el, '{%s}AllowanceChargeReasonCode' % NS['cbc']
            ).text = ac.allowance_charge_reason_code

        # AllowanceChargeReason
        etree.SubElement(
            ac_el, '{%s}AllowanceChargeReason' % NS['cbc']
        ).text = ac.reason

        # MultiplierFactorNumeric (porcentaje, opcional)
        if ac.percent is not None:
            etree.SubElement(
                ac_el, '{%s}MultiplierFactorNumeric' % NS['cbc']
            ).text = formato_dinero(ac.percent)

        # Amount
        amount_el = etree.SubElement(ac_el, '{%s}Amount' % NS['cbc'])
        amount_el.set('currencyID', currency)
        amount_el.text = formato_dinero(ac.amount or 0)

        # BaseAmount (opcional)
        if ac.base_amount is not None:
            base_el = etree.SubElement(ac_el, '{%s}BaseAmount' % NS['cbc'])
            base_el.set('currencyID', currency)
            base_el.text = formato_dinero(ac.base_amount)


def calculate_totals(allowance_charges: List[AllowanceCharge]) -> Tuple[float, float]:
    """
    Calcular totales de descuentos y cargos.

    Args:
        allowance_charges: Lista de descuentos/cargos

    Returns:
        Tuple (total_descuentos, total_cargos)
    """
    total_descuentos = sum(
        ac.amount or 0 for ac in allowance_charges if not ac.is_charge
    )
    total_cargos = sum(
        ac.amount or 0 for ac in allowance_charges if ac.is_charge
    )
    return truncar(total_descuentos), truncar(total_cargos)
