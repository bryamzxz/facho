# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constructor de notas debito UBL 2.1 para DIAN Colombia.
Basado en implementacion funcional aprobada por DIAN.
"""

from datetime import datetime
from typing import List
from dataclasses import dataclass
import hashlib

from lxml import etree

from .constants import NS, DIAN_PROFILE_ID_DEBIT_NOTE, DEBIT_NOTE_TYPE_CODE
from .invoice_builder import (
    InvoiceBuilder,
    InvoiceConfig,
    InvoiceData,
    InvoiceLine,
    Party,
    Address
)


# Motivos para notas debito (ResponseCode)
DEBIT_REASONS = {
    '1': 'Intereses',
    '2': 'Gastos por cobrar',
    '3': 'Cambio del valor',
    '4': 'Otros',
}


@dataclass
class DebitNoteData(InvoiceData):
    """Datos de nota debito."""
    billing_reference_id: str = ''  # Numero de factura referenciada
    billing_reference_uuid: str = ''  # CUFE de factura referenciada
    billing_reference_date: str = ''  # Fecha de factura referenciada
    discrepancy_response_code: str = '1'  # 1=Intereses, 2=Gastos, 3=Cambio valor, 4=Otros
    discrepancy_description: str = ''


class DebitNoteBuilder(InvoiceBuilder):
    """
    Constructor de notas debito electronicas UBL 2.1 para DIAN.

    Genera XML valido segun Anexo Tecnico v1.9.
    """

    def build(self, debit_note_data: DebitNoteData) -> etree._Element:
        """
        Construir nota debito XML.

        Args:
            debit_note_data: Datos de la nota debito

        Returns:
            Elemento XML de la nota debito
        """
        # Calcular totales
        subtotal = sum(
            line.quantity * line.unit_price
            for line in debit_note_data.lines
        )
        tax_iva = sum(
            line.quantity * line.unit_price * (line.tax_percent / 100)
            for line in debit_note_data.lines
        )
        total = subtotal + tax_iva

        # Calcular CUDE (para notas debito se usa CUDE, no CUFE)
        from ..client.dian_simple import calcular_software_security_code

        # CUDE = SHA384(NumDoc + FecDoc + HoraDoc + ValorBruto + 01 + ValorIVA + 04 + 0 + 03 + 0 +
        #               ValorTotal + NitEmisor + NumAdquiriente + SoftwarePIN + TipoAmbiente)
        cadena = (
            f"{debit_note_data.number}{debit_note_data.issue_date}{debit_note_data.issue_time}"
            f"{subtotal:.2f}01{tax_iva:.2f}04{0:.2f}03{0:.2f}"
            f"{total:.2f}{self.config.nit}{debit_note_data.customer.nit}"
            f"{self.config.software_pin}{self.config.environment}"
        )
        cude = hashlib.sha384(cadena.encode('utf-8')).hexdigest()

        software_security_code = calcular_software_security_code(
            self.config.software_id,
            self.config.software_pin,
            debit_note_data.number
        )

        return self._build_debit_note_xml(
            debit_note_data=debit_note_data,
            cude=cude,
            software_security_code=software_security_code,
            subtotal=subtotal,
            tax_iva=tax_iva,
            total=total
        )

    def _build_debit_note_xml(
        self,
        debit_note_data: DebitNoteData,
        cude: str,
        software_security_code: str,
        subtotal: float,
        tax_iva: float,
        total: float
    ) -> etree._Element:
        """Construir estructura XML de nota debito."""

        nsmap = {
            None: NS['nd'],
            'cac': NS['cac'],
            'cbc': NS['cbc'],
            'ext': NS['ext'],
            'sts': NS['sts'],
            'xsi': NS['xsi'],
        }

        debit_note = etree.Element('DebitNote', nsmap=nsmap)

        # UBLExtensions
        self._add_ubl_extensions_dn(
            debit_note, debit_note_data, cude, software_security_code
        )

        # Elementos basicos
        self._add_basic_elements_dn(debit_note, debit_note_data, cude)

        # DiscrepancyResponse (motivo de la nota)
        self._add_discrepancy_response(debit_note, debit_note_data)

        # Referencia a factura
        self._add_billing_reference(debit_note, debit_note_data)

        # Proveedor
        self._add_supplier(debit_note, debit_note_data.supplier)

        # Cliente
        self._add_customer(debit_note, debit_note_data.customer)

        # Medios de pago
        self._add_payment_means(debit_note, debit_note_data)

        # Impuestos totales
        self._add_tax_total(debit_note, subtotal, tax_iva)

        # Totales monetarios (RequestedMonetaryTotal para notas debito)
        self._add_monetary_total_dn(debit_note, subtotal, tax_iva, total)

        # Lineas
        self._add_debit_note_lines(debit_note, debit_note_data.lines)

        return debit_note

    def _add_ubl_extensions_dn(
        self,
        debit_note: etree._Element,
        debit_note_data: DebitNoteData,
        cude: str,
        software_security_code: str
    ):
        """Agregar UBLExtensions para nota debito."""
        from .constants import SCHEME_AGENCY_ATTRS, COUNTRY_ID_ATTRS, AUTHORIZATION_PROVIDER_ID
        from ..client.dian_simple import calcular_dv

        extensions = etree.SubElement(debit_note, '{%s}UBLExtensions' % NS['ext'])

        ext1 = etree.SubElement(extensions, '{%s}UBLExtension' % NS['ext'])
        ext1_content = etree.SubElement(ext1, '{%s}ExtensionContent' % NS['ext'])

        dian_ext = etree.SubElement(
            ext1_content,
            '{%s}DianExtensions' % NS['sts'],
            nsmap={'sts': NS['sts']}
        )

        # InvoiceSource
        inv_source = etree.SubElement(dian_ext, '{%s}InvoiceSource' % NS['sts'])
        id_country = etree.SubElement(inv_source, '{%s}IdentificationCode' % NS['cbc'])
        for attr, value in COUNTRY_ID_ATTRS.items():
            id_country.set(attr, value)
        id_country.text = 'CO'

        # SoftwareProvider
        software_prov = etree.SubElement(dian_ext, '{%s}SoftwareProvider' % NS['sts'])
        prov_id = etree.SubElement(software_prov, '{%s}ProviderID' % NS['sts'])
        prov_id.set('schemeAgencyID', '195')
        prov_id.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        prov_id.set('schemeID', str(calcular_dv(self.config.nit)))
        prov_id.set('schemeName', '31')
        prov_id.text = self.config.nit

        soft_id = etree.SubElement(software_prov, '{%s}SoftwareID' % NS['sts'])
        soft_id.set('schemeAgencyID', '195')
        soft_id.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        soft_id.text = self.config.software_id

        # SoftwareSecurityCode
        soft_sec = etree.SubElement(dian_ext, '{%s}SoftwareSecurityCode' % NS['sts'])
        soft_sec.set('schemeAgencyID', '195')
        soft_sec.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        soft_sec.text = software_security_code

        # AuthorizationProvider
        auth_prov = etree.SubElement(dian_ext, '{%s}AuthorizationProvider' % NS['sts'])
        auth_prov_id = etree.SubElement(auth_prov, '{%s}AuthorizationProviderID' % NS['sts'])
        auth_prov_id.set('schemeAgencyID', '195')
        auth_prov_id.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        auth_prov_id.set('schemeID', '4')
        auth_prov_id.set('schemeName', '31')
        auth_prov_id.text = AUTHORIZATION_PROVIDER_ID

        # QRCode
        qr_base = 'https://catalogo-vpfe-hab.dian.gov.co' if self.config.environment == '2' \
            else 'https://catalogo-vpfe.dian.gov.co'
        qr_code = etree.SubElement(dian_ext, '{%s}QRCode' % NS['sts'])
        qr_code.text = f"{qr_base}/document/searchqr?documentkey={cude}"

        # Extension 2: Signature
        ext2 = etree.SubElement(extensions, '{%s}UBLExtension' % NS['ext'])
        etree.SubElement(ext2, '{%s}ExtensionContent' % NS['ext'])

    def _add_basic_elements_dn(
        self,
        debit_note: etree._Element,
        debit_note_data: DebitNoteData,
        cude: str
    ):
        """Agregar elementos basicos de nota debito."""
        from .constants import DIAN_UBL_VERSION, DIAN_CUSTOMIZATION_ID

        etree.SubElement(debit_note, '{%s}UBLVersionID' % NS['cbc']).text = DIAN_UBL_VERSION
        # CustomizationID para notas debito es 30
        etree.SubElement(debit_note, '{%s}CustomizationID' % NS['cbc']).text = '30'
        etree.SubElement(debit_note, '{%s}ProfileID' % NS['cbc']).text = DIAN_PROFILE_ID_DEBIT_NOTE
        etree.SubElement(
            debit_note, '{%s}ProfileExecutionID' % NS['cbc']
        ).text = self.config.environment
        etree.SubElement(debit_note, '{%s}ID' % NS['cbc']).text = debit_note_data.number

        uuid_el = etree.SubElement(debit_note, '{%s}UUID' % NS['cbc'])
        uuid_el.set('schemeID', self.config.environment)
        uuid_el.set('schemeName', 'CUDE-SHA384')
        uuid_el.text = cude

        etree.SubElement(debit_note, '{%s}IssueDate' % NS['cbc']).text = debit_note_data.issue_date
        etree.SubElement(debit_note, '{%s}IssueTime' % NS['cbc']).text = debit_note_data.issue_time

        dn_type = etree.SubElement(debit_note, '{%s}DebitNoteTypeCode' % NS['cbc'])
        dn_type.text = DEBIT_NOTE_TYPE_CODE

        etree.SubElement(debit_note, '{%s}Note' % NS['cbc']).text = debit_note_data.note

        doc_currency = etree.SubElement(debit_note, '{%s}DocumentCurrencyCode' % NS['cbc'])
        doc_currency.set('listAgencyID', '6')
        doc_currency.set('listAgencyName', 'United Nations Economic Commission for Europe')
        doc_currency.set('listID', 'ISO 4217 Alpha')
        doc_currency.text = 'COP'

        etree.SubElement(
            debit_note, '{%s}LineCountNumeric' % NS['cbc']
        ).text = str(len(debit_note_data.lines))

    def _add_discrepancy_response(
        self,
        debit_note: etree._Element,
        debit_note_data: DebitNoteData
    ):
        """Agregar respuesta de discrepancia."""
        disc_resp = etree.SubElement(debit_note, '{%s}DiscrepancyResponse' % NS['cac'])
        etree.SubElement(
            disc_resp, '{%s}ReferenceID' % NS['cbc']
        ).text = debit_note_data.billing_reference_id
        etree.SubElement(
            disc_resp, '{%s}ResponseCode' % NS['cbc']
        ).text = debit_note_data.discrepancy_response_code

        description = debit_note_data.discrepancy_description or \
            DEBIT_REASONS.get(debit_note_data.discrepancy_response_code, 'Otros')
        etree.SubElement(disc_resp, '{%s}Description' % NS['cbc']).text = description

    def _add_billing_reference(
        self,
        debit_note: etree._Element,
        debit_note_data: DebitNoteData
    ):
        """Agregar referencia a factura original."""
        billing_ref = etree.SubElement(debit_note, '{%s}BillingReference' % NS['cac'])
        inv_doc_ref = etree.SubElement(billing_ref, '{%s}InvoiceDocumentReference' % NS['cac'])
        etree.SubElement(
            inv_doc_ref, '{%s}ID' % NS['cbc']
        ).text = debit_note_data.billing_reference_id

        uuid_ref = etree.SubElement(inv_doc_ref, '{%s}UUID' % NS['cbc'])
        uuid_ref.set('schemeName', 'CUFE-SHA384')
        uuid_ref.text = debit_note_data.billing_reference_uuid

        etree.SubElement(
            inv_doc_ref, '{%s}IssueDate' % NS['cbc']
        ).text = debit_note_data.billing_reference_date

    def _add_monetary_total_dn(
        self,
        debit_note: etree._Element,
        subtotal: float,
        tax_iva: float,
        total: float
    ):
        """Agregar totales monetarios para nota debito (RequestedMonetaryTotal)."""
        monetary = etree.SubElement(debit_note, '{%s}RequestedMonetaryTotal' % NS['cac'])

        for tag, value in [
            ('LineExtensionAmount', subtotal),
            ('TaxExclusiveAmount', subtotal),
            ('TaxInclusiveAmount', total),
            ('AllowanceTotalAmount', 0),
            ('ChargeTotalAmount', 0),
            ('PayableAmount', total),
        ]:
            el = etree.SubElement(monetary, '{%s}%s' % (NS['cbc'], tag))
            el.set('currencyID', 'COP')
            el.text = f"{value:.2f}"

    def _add_debit_note_lines(
        self,
        debit_note: etree._Element,
        lines: List[InvoiceLine]
    ):
        """Agregar lineas de nota debito."""
        for idx, line_data in enumerate(lines, 1):
            line_total = line_data.quantity * line_data.unit_price
            line_tax = line_total * (line_data.tax_percent / 100)

            line = etree.SubElement(debit_note, '{%s}DebitNoteLine' % NS['cac'])
            etree.SubElement(line, '{%s}ID' % NS['cbc']).text = str(idx)

            qty = etree.SubElement(line, '{%s}DebitedQuantity' % NS['cbc'])
            qty.set('unitCode', line_data.unit_code)
            qty.text = f'{line_data.quantity:.2f}'

            line_ext = etree.SubElement(line, '{%s}LineExtensionAmount' % NS['cbc'])
            line_ext.set('currencyID', 'COP')
            line_ext.text = f"{line_total:.2f}"

            # TaxTotal de linea
            line_tax_el = etree.SubElement(line, '{%s}TaxTotal' % NS['cac'])
            line_tax_amt = etree.SubElement(line_tax_el, '{%s}TaxAmount' % NS['cbc'])
            line_tax_amt.set('currencyID', 'COP')
            line_tax_amt.text = f"{line_tax:.2f}"

            line_round = etree.SubElement(line_tax_el, '{%s}RoundingAmount' % NS['cbc'])
            line_round.set('currencyID', 'COP')
            line_round.text = '0.00'

            line_tax_sub = etree.SubElement(line_tax_el, '{%s}TaxSubtotal' % NS['cac'])
            line_taxable = etree.SubElement(line_tax_sub, '{%s}TaxableAmount' % NS['cbc'])
            line_taxable.set('currencyID', 'COP')
            line_taxable.text = f"{line_total:.2f}"

            line_tax_amt2 = etree.SubElement(line_tax_sub, '{%s}TaxAmount' % NS['cbc'])
            line_tax_amt2.set('currencyID', 'COP')
            line_tax_amt2.text = f"{line_tax:.2f}"

            line_tax_cat = etree.SubElement(line_tax_sub, '{%s}TaxCategory' % NS['cac'])
            etree.SubElement(line_tax_cat, '{%s}Percent' % NS['cbc']).text = f'{line_data.tax_percent:.2f}'
            line_tax_sch = etree.SubElement(line_tax_cat, '{%s}TaxScheme' % NS['cac'])
            etree.SubElement(line_tax_sch, '{%s}ID' % NS['cbc']).text = '01'
            etree.SubElement(line_tax_sch, '{%s}Name' % NS['cbc']).text = 'IVA'

            # Item
            item = etree.SubElement(line, '{%s}Item' % NS['cac'])
            etree.SubElement(item, '{%s}Description' % NS['cbc']).text = line_data.description

            if line_data.item_id:
                item_id_el = etree.SubElement(item, '{%s}SellersItemIdentification' % NS['cac'])
                etree.SubElement(item_id_el, '{%s}ID' % NS['cbc']).text = line_data.item_id

            item_std = etree.SubElement(item, '{%s}StandardItemIdentification' % NS['cac'])
            std_id = etree.SubElement(item_std, '{%s}ID' % NS['cbc'])
            std_id.set('schemeID', line_data.item_scheme_id)
            std_id.set('schemeAgencyID', '195')
            std_id.set('schemeName', line_data.item_scheme_name)
            std_id.text = line_data.item_id or f'ITEM{idx:03d}'

            # Price
            price = etree.SubElement(line, '{%s}Price' % NS['cac'])
            price_amt = etree.SubElement(price, '{%s}PriceAmount' % NS['cbc'])
            price_amt.set('currencyID', 'COP')
            price_amt.text = f"{line_data.unit_price:.2f}"
            etree.SubElement(price, '{%s}BaseQuantity' % NS['cbc']).text = '1.00'
