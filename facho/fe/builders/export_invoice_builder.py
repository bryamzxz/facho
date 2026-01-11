# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constructor de Factura de Exportacion (tipo 02) para DIAN Colombia.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from lxml import etree

from .constants import (
    NS,
    SCHEME_AGENCY_ATTRS,
    DIAN_UBL_VERSION,
    DIAN_CUSTOMIZATION_ID,
    COUNTRY_ID_ATTRS,
    AUTHORIZATION_PROVIDER_ID,
)
from .taxes import (
    Tax,
    TaxTotal,
    agrupar_impuestos,
    separar_impuestos_retenciones,
    calcular_totales_impuestos,
    truncar,
    formato_dinero,
)
from .invoice_builder import InvoiceBuilder, InvoiceConfig, InvoiceLine, Party, Address
from .exceptions import ValidationError, XmlBuildError
from .validators import validate_before_build
from ..client.dian_simple import (
    calcular_dv,
    calcular_cufe_flexible,
    calcular_software_security_code,
)


EXPORT_INVOICE_TYPE_CODE = '02'
EXPORT_INVOICE_PROFILE_ID = 'DIAN 2.1: Factura Electronica de Exportacion'

# Incoterms soportados
INCOTERMS = {
    'EXW': 'Ex Works',
    'FCA': 'Free Carrier',
    'FAS': 'Free Alongside Ship',
    'FOB': 'Free On Board',
    'CFR': 'Cost and Freight',
    'CIF': 'Cost, Insurance and Freight',
    'CPT': 'Carriage Paid To',
    'CIP': 'Carriage and Insurance Paid To',
    'DAP': 'Delivered at Place',
    'DPU': 'Delivered at Place Unloaded',
    'DDP': 'Delivered Duty Paid',
}

# Monedas soportadas
CURRENCIES = {
    'COP': 'Peso Colombiano',
    'USD': 'Dolar Estadounidense',
    'EUR': 'Euro',
    'GBP': 'Libra Esterlina',
    'JPY': 'Yen Japones',
    'CHF': 'Franco Suizo',
}


@dataclass
class DeliveryTerms:
    """
    Terminos de entrega (Incoterms).

    Attributes:
        incoterm: Codigo Incoterm (EXW, FOB, CIF, etc.)
        location: Lugar de entrega
    """
    incoterm: str
    location: str = ''


@dataclass
class DeliveryInfo:
    """
    Informacion de entrega.

    Attributes:
        country_code: Codigo ISO del pais de destino
        country_name: Nombre del pais de destino
        city: Ciudad de destino (opcional)
        address: Direccion de entrega (opcional)
        delivery_date: Fecha de entrega (opcional, YYYY-MM-DD)
    """
    country_code: str
    country_name: str
    city: str = ''
    address: str = ''
    delivery_date: str = None


@dataclass
class ExchangeRate:
    """
    Tasa de cambio.

    Attributes:
        source_currency: Moneda de origen (ej: USD)
        target_currency: Moneda de destino (default: COP)
        rate: Tasa de cambio
        rate_date: Fecha de la tasa (opcional, YYYY-MM-DD)
    """
    source_currency: str
    target_currency: str = 'COP'
    rate: float = 1.0
    rate_date: str = None


@dataclass
class ExportInvoiceData:
    """
    Datos de factura de exportacion.

    Attributes:
        number: Numero de factura
        issue_date: Fecha de emision (YYYY-MM-DD)
        issue_time: Hora de emision (HH:MM:SS-05:00)
        due_date: Fecha de vencimiento (opcional)
        note: Nota de la factura
        supplier: Datos del vendedor/exportador
        customer: Datos del comprador/importador
        lines: Lineas de la factura
        currency: Moneda de la factura (default: USD)
        exchange_rate: Tasa de cambio (opcional)
        delivery: Informacion de entrega (opcional)
        delivery_terms: Terminos de entrega/Incoterms (opcional)
        order_reference: Referencia de orden de compra (opcional)
    """
    number: str
    issue_date: str
    issue_time: str
    due_date: str = None
    note: str = 'Factura de exportacion'
    supplier: Party = None
    customer: Party = None
    lines: List[InvoiceLine] = field(default_factory=list)
    currency: str = 'USD'
    exchange_rate: ExchangeRate = None
    delivery: DeliveryInfo = None
    delivery_terms: DeliveryTerms = None
    order_reference: str = None


class ExportInvoiceBuilder(InvoiceBuilder):
    """
    Constructor de Factura de Exportacion.

    La factura de exportacion se utiliza para ventas al exterior,
    tipicamente con IVA 0% y moneda extranjera.

    Example:
        customer = Party(
            nit='123456789',
            scheme_name='42',  # Documento extranjero
            address=Address(
                country_code='US',
                country_name='Estados Unidos',
                ...
            )
        )

        data = ExportInvoiceData(
            number='EXP0001',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
            currency='USD',
            exchange_rate=ExchangeRate(source_currency='USD', rate=4000.0),
            delivery=DeliveryInfo(country_code='US', country_name='Estados Unidos'),
            delivery_terms=DeliveryTerms(incoterm='FOB', location='Cartagena'),
            supplier=supplier,
            customer=customer,
            lines=[InvoiceLine(..., taxes=[Tax.iva_0(100000)])]
        )

        builder = ExportInvoiceBuilder(config)
        xml = builder.build(data)
    """

    def build(self, data: ExportInvoiceData) -> etree._Element:
        """
        Construir XML de factura de exportacion.

        Args:
            data: Datos de la factura de exportacion

        Returns:
            Elemento XML de la factura
        """
        try:
            validate_before_build(data, self.config, "factura de exportacion")

            currency = data.currency or 'USD'

            # Calcular subtotal
            subtotal = truncar(sum(
                line.get_line_total() for line in data.lines
            ))

            # Recolectar todos los impuestos
            all_taxes: List[Tax] = []
            for line in data.lines:
                all_taxes.extend(line.taxes)

            # Separar impuestos de retenciones
            impuestos, retenciones = separar_impuestos_retenciones(all_taxes)

            # Calcular totales
            totales_impuestos = calcular_totales_impuestos(impuestos)
            total_impuestos = truncar(sum(totales_impuestos.values()))

            # Agrupar para XML
            impuestos_agrupados = agrupar_impuestos(impuestos)

            # Total
            total = truncar(subtotal + total_impuestos)

            # Convertir a COP para CUFE si es otra moneda
            rate = data.exchange_rate.rate if data.exchange_rate else 1.0
            if currency != 'COP':
                subtotal_cop = truncar(subtotal * rate)
                total_cop = truncar(total * rate)
                impuestos_cop = {
                    k: truncar(v * rate)
                    for k, v in totales_impuestos.items()
                }
            else:
                subtotal_cop = subtotal
                total_cop = total
                impuestos_cop = totales_impuestos

            # Calcular CUFE
            cufe = calcular_cufe_flexible(
                numero=data.number,
                fecha_emision=data.issue_date,
                hora_emision=data.issue_time,
                subtotal=subtotal_cop,
                impuestos=impuestos_cop,
                total=total_cop,
                nit_emisor=self.config.nit,
                nit_adquiriente=data.customer.nit,
                clave_tecnica=self.config.technical_key,
                tipo_ambiente=self.config.environment
            )

            software_security_code = calcular_software_security_code(
                self.config.software_id,
                self.config.software_pin,
                data.number
            )

            # Construir XML
            nsmap = {
                None: NS['fe'],
                'cac': NS['cac'],
                'cbc': NS['cbc'],
                'ext': NS['ext'],
                'sts': NS['sts'],
                'xsi': NS['xsi'],
            }

            doc = etree.Element('Invoice', nsmap=nsmap)

            # UBLExtensions
            self._add_ubl_extensions(doc, data, cufe, software_security_code)

            # Campos principales
            etree.SubElement(
                doc, '{%s}UBLVersionID' % NS['cbc']
            ).text = DIAN_UBL_VERSION
            etree.SubElement(
                doc, '{%s}CustomizationID' % NS['cbc']
            ).text = DIAN_CUSTOMIZATION_ID
            etree.SubElement(
                doc, '{%s}ProfileID' % NS['cbc']
            ).text = EXPORT_INVOICE_PROFILE_ID
            etree.SubElement(
                doc, '{%s}ProfileExecutionID' % NS['cbc']
            ).text = self.config.environment
            etree.SubElement(doc, '{%s}ID' % NS['cbc']).text = data.number

            # UUID (CUFE)
            uuid_el = etree.SubElement(doc, '{%s}UUID' % NS['cbc'])
            uuid_el.set('schemeID', self.config.environment)
            uuid_el.set('schemeName', 'CUFE-SHA384')
            uuid_el.text = cufe

            # Fechas
            etree.SubElement(
                doc, '{%s}IssueDate' % NS['cbc']
            ).text = data.issue_date
            etree.SubElement(
                doc, '{%s}IssueTime' % NS['cbc']
            ).text = data.issue_time
            if data.due_date:
                etree.SubElement(
                    doc, '{%s}DueDate' % NS['cbc']
                ).text = data.due_date

            # Tipo de documento
            etree.SubElement(
                doc, '{%s}InvoiceTypeCode' % NS['cbc']
            ).text = EXPORT_INVOICE_TYPE_CODE

            # Nota
            if data.note:
                etree.SubElement(doc, '{%s}Note' % NS['cbc']).text = data.note

            # Moneda del documento
            doc_currency = etree.SubElement(
                doc, '{%s}DocumentCurrencyCode' % NS['cbc']
            )
            doc_currency.set('listAgencyID', '6')
            doc_currency.set(
                'listAgencyName',
                'United Nations Economic Commission for Europe'
            )
            doc_currency.set('listID', 'ISO 4217 Alpha')
            doc_currency.text = currency

            # Cantidad de lineas
            etree.SubElement(
                doc, '{%s}LineCountNumeric' % NS['cbc']
            ).text = str(len(data.lines))

            # Order Reference (opcional)
            if data.order_reference:
                order_ref = etree.SubElement(
                    doc, '{%s}OrderReference' % NS['cac']
                )
                etree.SubElement(
                    order_ref, '{%s}ID' % NS['cbc']
                ).text = data.order_reference

            # Partes
            self._add_supplier(doc, data.supplier)
            self._add_customer(doc, data.customer)

            # Delivery (informacion de entrega)
            if data.delivery:
                self._add_delivery(doc, data.delivery)

            # Delivery Terms (Incoterms)
            if data.delivery_terms:
                self._add_delivery_terms(doc, data.delivery_terms)

            # PaymentExchangeRate (tasa de cambio)
            if data.exchange_rate and currency != 'COP':
                self._add_exchange_rate(doc, data.exchange_rate)

            # Medio de pago
            self._add_payment_means(doc, data)

            # Impuestos
            self._add_tax_totals(doc, impuestos_agrupados, currency)

            # Totales monetarios
            self._add_monetary_total_export(
                doc, subtotal, total_impuestos, total, currency
            )

            # Lineas
            self._add_invoice_lines_export(doc, data.lines, currency)

            return doc

        except ValidationError:
            raise
        except Exception as e:
            raise XmlBuildError(
                f"Error construyendo factura de exportacion: {str(e)}"
            )

    def _add_delivery(self, doc: etree._Element, delivery: DeliveryInfo):
        """Agregar informacion de entrega."""
        del_el = etree.SubElement(doc, '{%s}Delivery' % NS['cac'])

        if delivery.delivery_date:
            etree.SubElement(
                del_el, '{%s}ActualDeliveryDate' % NS['cbc']
            ).text = delivery.delivery_date

        del_loc = etree.SubElement(del_el, '{%s}DeliveryLocation' % NS['cac'])
        del_addr = etree.SubElement(del_loc, '{%s}Address' % NS['cac'])

        if delivery.city:
            etree.SubElement(
                del_addr, '{%s}CityName' % NS['cbc']
            ).text = delivery.city

        if delivery.address:
            addr_line = etree.SubElement(
                del_addr, '{%s}AddressLine' % NS['cac']
            )
            etree.SubElement(
                addr_line, '{%s}Line' % NS['cbc']
            ).text = delivery.address

        country = etree.SubElement(del_addr, '{%s}Country' % NS['cac'])
        etree.SubElement(
            country, '{%s}IdentificationCode' % NS['cbc']
        ).text = delivery.country_code
        name = etree.SubElement(country, '{%s}Name' % NS['cbc'])
        name.set('languageID', 'es')
        name.text = delivery.country_name

    def _add_delivery_terms(self, doc: etree._Element, terms: DeliveryTerms):
        """Agregar terminos de entrega (Incoterms)."""
        dt_el = etree.SubElement(doc, '{%s}DeliveryTerms' % NS['cac'])
        etree.SubElement(dt_el, '{%s}ID' % NS['cbc']).text = terms.incoterm
        if terms.location:
            etree.SubElement(
                dt_el, '{%s}SpecialTerms' % NS['cbc']
            ).text = terms.location

    def _add_exchange_rate(self, doc: etree._Element, exchange: ExchangeRate):
        """Agregar tasa de cambio."""
        er_el = etree.SubElement(doc, '{%s}PaymentExchangeRate' % NS['cac'])
        etree.SubElement(
            er_el, '{%s}SourceCurrencyCode' % NS['cbc']
        ).text = exchange.source_currency
        etree.SubElement(
            er_el, '{%s}SourceCurrencyBaseRate' % NS['cbc']
        ).text = '1.00'
        etree.SubElement(
            er_el, '{%s}TargetCurrencyCode' % NS['cbc']
        ).text = exchange.target_currency
        etree.SubElement(
            er_el, '{%s}TargetCurrencyBaseRate' % NS['cbc']
        ).text = '1.00'
        etree.SubElement(
            er_el, '{%s}CalculationRate' % NS['cbc']
        ).text = formato_dinero(exchange.rate)
        if exchange.rate_date:
            etree.SubElement(
                er_el, '{%s}Date' % NS['cbc']
            ).text = exchange.rate_date

    def _add_monetary_total_export(
        self,
        doc: etree._Element,
        subtotal: float,
        total_impuestos: float,
        total: float,
        currency: str
    ):
        """Agregar totales monetarios para exportacion."""
        monetary = etree.SubElement(doc, '{%s}LegalMonetaryTotal' % NS['cac'])
        for tag, value in [
            ('LineExtensionAmount', subtotal),
            ('TaxExclusiveAmount', subtotal),
            ('TaxInclusiveAmount', total),
            ('AllowanceTotalAmount', 0),
            ('ChargeTotalAmount', 0),
            ('PrepaidAmount', 0),
            ('PayableAmount', total),
        ]:
            el = etree.SubElement(monetary, '{%s}%s' % (NS['cbc'], tag))
            el.set('currencyID', currency)
            el.text = formato_dinero(value)

    def _add_invoice_lines_export(
        self,
        doc: etree._Element,
        lines: List[InvoiceLine],
        currency: str
    ):
        """Agregar lineas con moneda especificada."""
        for i, line_data in enumerate(lines, 1):
            line = etree.SubElement(doc, '{%s}InvoiceLine' % NS['cac'])
            etree.SubElement(line, '{%s}ID' % NS['cbc']).text = str(i)

            qty = etree.SubElement(line, '{%s}InvoicedQuantity' % NS['cbc'])
            qty.set('unitCode', line_data.unit_code)
            qty.text = formato_dinero(line_data.quantity)

            line_total = line_data.get_line_total()
            line_ext = etree.SubElement(
                line, '{%s}LineExtensionAmount' % NS['cbc']
            )
            line_ext.set('currencyID', currency)
            line_ext.text = formato_dinero(line_total)

            # TaxTotal de linea
            if line_data.taxes:
                for tax in line_data.taxes:
                    if not tax.is_withholding:
                        self._add_line_tax_export(line, tax, currency)

            # Item
            item = etree.SubElement(line, '{%s}Item' % NS['cac'])
            etree.SubElement(
                item, '{%s}Description' % NS['cbc']
            ).text = line_data.description

            if line_data.item_id:
                item_id_el = etree.SubElement(
                    item, '{%s}SellersItemIdentification' % NS['cac']
                )
                etree.SubElement(
                    item_id_el, '{%s}ID' % NS['cbc']
                ).text = line_data.item_id

            item_std = etree.SubElement(
                item, '{%s}StandardItemIdentification' % NS['cac']
            )
            std_id = etree.SubElement(item_std, '{%s}ID' % NS['cbc'])
            std_id.set('schemeID', line_data.item_scheme_id)
            std_id.set('schemeAgencyID', '195')
            std_id.set('schemeName', line_data.item_scheme_name)
            std_id.text = line_data.item_id or f'ITEM{i:03d}'

            # Price
            price = etree.SubElement(line, '{%s}Price' % NS['cac'])
            price_amt = etree.SubElement(price, '{%s}PriceAmount' % NS['cbc'])
            price_amt.set('currencyID', currency)
            price_amt.text = formato_dinero(line_data.unit_price)

            base_qty = etree.SubElement(price, '{%s}BaseQuantity' % NS['cbc'])
            base_qty.set('unitCode', line_data.unit_code)
            base_qty.text = '1.00'

    def _add_line_tax_export(
        self,
        line: etree._Element,
        tax: Tax,
        currency: str
    ):
        """Agregar impuesto de linea."""
        tax_total = etree.SubElement(line, '{%s}TaxTotal' % NS['cac'])
        tax_amt = etree.SubElement(tax_total, '{%s}TaxAmount' % NS['cbc'])
        tax_amt.set('currencyID', currency)
        tax_amt.text = formato_dinero(tax.amount)

        rounding = etree.SubElement(
            tax_total, '{%s}RoundingAmount' % NS['cbc']
        )
        rounding.set('currencyID', currency)
        rounding.text = '0.00'

        tax_sub = etree.SubElement(tax_total, '{%s}TaxSubtotal' % NS['cac'])
        taxable = etree.SubElement(tax_sub, '{%s}TaxableAmount' % NS['cbc'])
        taxable.set('currencyID', currency)
        taxable.text = formato_dinero(tax.taxable_amount)

        tax_amt2 = etree.SubElement(tax_sub, '{%s}TaxAmount' % NS['cbc'])
        tax_amt2.set('currencyID', currency)
        tax_amt2.text = formato_dinero(tax.amount)

        tax_cat = etree.SubElement(tax_sub, '{%s}TaxCategory' % NS['cac'])
        etree.SubElement(
            tax_cat, '{%s}Percent' % NS['cbc']
        ).text = formato_dinero(tax.percent)

        tax_sch = etree.SubElement(tax_cat, '{%s}TaxScheme' % NS['cac'])
        etree.SubElement(tax_sch, '{%s}ID' % NS['cbc']).text = tax.code
        etree.SubElement(tax_sch, '{%s}Name' % NS['cbc']).text = tax.name
