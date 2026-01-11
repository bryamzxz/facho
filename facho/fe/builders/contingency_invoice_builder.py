# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constructor de Factura de Contingencia (tipo 04) para DIAN Colombia.

Se usa cuando los servicios DIAN estan caidos y se debe facturar
con talonarios de contingencia.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from lxml import etree

from .constants import (
    NS,
    SCHEME_AGENCY_ATTRS,
    DIAN_UBL_VERSION,
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


CONTINGENCY_TYPE_CODE = '04'
CONTINGENCY_PROFILE_ID = 'DIAN 2.1: Factura Electronica de Contingencia'
CONTINGENCY_CUSTOMIZATION_ID = '04'


@dataclass
class ContingencyInvoiceData:
    """
    Datos de factura de contingencia.

    Attributes:
        number: Numero del documento de contingencia
        issue_date: Fecha de emision original (YYYY-MM-DD)
        issue_time: Hora de emision original (HH:MM:SS-05:00)
        due_date: Fecha de vencimiento (opcional)
        note: Nota de la factura
        supplier: Datos del proveedor
        customer: Datos del cliente
        lines: Lineas de la factura
        contingency_date: Fecha en que ocurrio la contingencia (YYYY-MM-DD)
        contingency_reason: Razon de la contingencia
    """
    number: str
    issue_date: str
    issue_time: str
    due_date: str = None
    note: str = 'Factura de contingencia'
    supplier: Party = None
    customer: Party = None
    lines: List[InvoiceLine] = field(default_factory=list)
    contingency_date: str = None
    contingency_reason: str = 'Falla tecnica en servicios DIAN'


class ContingencyInvoiceBuilder(InvoiceBuilder):
    """
    Constructor de Factura de Contingencia.

    Se utiliza cuando:
    - Los servicios DIAN estan caidos
    - Hay problemas de conectividad
    - Se debe facturar y no hay acceso a DIAN

    La factura de contingencia se transmite despues cuando
    los servicios se restablecen.

    Example:
        data = ContingencyInvoiceData(
            number='CONT0001',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
            contingency_date='2024-01-15',
            contingency_reason='Servicios DIAN no disponibles',
            supplier=supplier,
            customer=customer,
            lines=[...]
        )

        builder = ContingencyInvoiceBuilder(config)
        xml = builder.build(data)
    """

    def build(self, data: ContingencyInvoiceData) -> etree._Element:
        """
        Construir XML de factura de contingencia.

        Args:
            data: Datos de la factura de contingencia

        Returns:
            Elemento XML de la factura
        """
        try:
            validate_before_build(data, self.config, "factura de contingencia")

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
            retenciones_agrupadas = agrupar_impuestos(retenciones)

            # Total
            total = truncar(subtotal + total_impuestos)

            # Calcular CUFE
            cufe = calcular_cufe_flexible(
                numero=data.number,
                fecha_emision=data.issue_date,
                hora_emision=data.issue_time,
                subtotal=subtotal,
                impuestos=totales_impuestos,
                total=total,
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
            ).text = CONTINGENCY_CUSTOMIZATION_ID
            etree.SubElement(
                doc, '{%s}ProfileID' % NS['cbc']
            ).text = CONTINGENCY_PROFILE_ID
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
            ).text = CONTINGENCY_TYPE_CODE

            # Nota con razon de contingencia
            note_text = data.note
            if data.contingency_reason:
                note_text = f"{note_text}. Contingencia: {data.contingency_reason}"
            if data.contingency_date:
                note_text = (
                    f"{note_text}. Fecha contingencia: {data.contingency_date}"
                )
            etree.SubElement(doc, '{%s}Note' % NS['cbc']).text = note_text

            # Moneda
            doc_currency = etree.SubElement(
                doc, '{%s}DocumentCurrencyCode' % NS['cbc']
            )
            doc_currency.set('listAgencyID', '6')
            doc_currency.set(
                'listAgencyName',
                'United Nations Economic Commission for Europe'
            )
            doc_currency.set('listID', 'ISO 4217 Alpha')
            doc_currency.text = 'COP'

            # Cantidad de lineas
            etree.SubElement(
                doc, '{%s}LineCountNumeric' % NS['cbc']
            ).text = str(len(data.lines))

            # Partes
            self._add_supplier(doc, data.supplier)
            self._add_customer(doc, data.customer)

            # Medio de pago
            self._add_payment_means(doc, data)

            # Impuestos
            self._add_tax_totals(doc, impuestos_agrupados)

            # Retenciones
            if retenciones_agrupadas:
                self._add_withholding_tax_totals(doc, retenciones_agrupadas)

            # Totales monetarios
            self._add_monetary_total(doc, subtotal, total_impuestos, total)

            # Lineas
            self._add_invoice_lines(doc, data.lines)

            return doc

        except ValidationError:
            raise
        except Exception as e:
            raise XmlBuildError(
                f"Error construyendo factura de contingencia: {str(e)}"
            )
