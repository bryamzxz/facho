# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constructor de notas credito UBL 2.1 para DIAN Colombia.

Diferencias clave vs Factura:
- CustomizationID: '20' (no '10')
- ProfileID: 'DIAN 2.1: Nota Credito de Factura Electronica de Venta'
- Usa CUDE (no CUFE) calculado con SoftwarePIN en lugar de ClaveTecnica
- Requiere DiscrepancyResponse con ResponseCode y Description
- Requiere BillingReference con UUID y fecha de factura referenciada
- Lineas son CreditNoteLine con CreditedQuantity
"""

from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from lxml import etree

from .constants import (
    NS, DIAN_PROFILE_ID_CREDIT_NOTE, CUSTOMIZATION_ID_CREDIT_NOTE,
    CREDIT_NOTE_RESPONSE_CODES
)
from .cufe import CufeInput, calculate_cude, calculate_software_security_code
from .validators import validate_credit_note_reference
from .invoice_builder import (
    InvoiceBuilder,
    InvoiceConfig,
    InvoiceData,
    InvoiceLine,
    Party,
    Address
)


@dataclass
class CreditNoteData(InvoiceData):
    """
    Datos de nota credito.

    Attributes:
        billing_reference_id: Numero de factura referenciada (ej: 'SETP990000001')
        billing_reference_uuid: CUFE de la factura referenciada (96 caracteres)
        billing_reference_date: Fecha de la factura referenciada (YYYY-MM-DD)
        discrepancy_response_code: Codigo de respuesta DIAN:
            - '1': Devolucion parcial de bienes
            - '2': Anulacion de factura (default)
            - '3': Rebaja o descuento
            - '4': Ajuste de precio
            - '5': Otros
        discrepancy_description: Descripcion del motivo (opcional)
    """
    billing_reference_id: str = ''
    billing_reference_uuid: str = ''
    billing_reference_date: str = ''
    discrepancy_response_code: str = '2'
    discrepancy_description: str = ''

    @property
    def response_description(self) -> str:
        """Obtener descripcion del codigo de respuesta."""
        if self.discrepancy_description:
            return self.discrepancy_description
        return CREDIT_NOTE_RESPONSE_CODES.get(
            self.discrepancy_response_code, 'Nota credito'
        )

    def validate_reference(self) -> List[str]:
        """Validar la referencia a la factura original."""
        return validate_credit_note_reference(
            self.billing_reference_id,
            self.billing_reference_uuid,
            self.billing_reference_date,
            self.discrepancy_response_code
        )


class CreditNoteBuilder(InvoiceBuilder):
    """
    Constructor de notas credito electronicas UBL 2.1 para DIAN.
    """

    def build(self, credit_note_data: CreditNoteData, validate: bool = True) -> etree._Element:
        """
        Construir nota credito XML.

        Args:
            credit_note_data: Datos de la nota credito
            validate: Si se deben validar los datos antes de construir

        Returns:
            Elemento XML de la nota credito

        Raises:
            ValidationError: Si los datos no son validos
        """
        # Validar referencia si se solicita
        if validate:
            errors = credit_note_data.validate_reference()
            if errors:
                from .exceptions import ValidationError
                raise ValidationError(
                    "Referencia de nota credito invalida",
                    errors=errors
                )

        # Calcular totales
        subtotal = sum(
            line.quantity * line.unit_price
            for line in credit_note_data.lines
        )
        tax_iva = sum(
            line.quantity * line.unit_price * (line.tax_percent / 100)
            for line in credit_note_data.lines
        )
        total = subtotal + tax_iva

        # Calcular CUDE usando el modulo cufe.py
        # CUDE usa SoftwarePIN en lugar de ClaveTecnica
        cufe_input = CufeInput(
            number=credit_note_data.number,
            issue_date=credit_note_data.issue_date,
            issue_time=credit_note_data.issue_time,
            subtotal=subtotal,
            iva_amount=tax_iva,
            inc_amount=0.0,
            ica_amount=0.0,
            total=total,
            supplier_nit=self.config.nit,
            customer_nit=credit_note_data.customer.nit,
            technical_key=self.config.software_pin,  # PIN para CUDE
            environment=self.config.environment,
        )
        cude = calculate_cude(cufe_input)

        software_security_code = calculate_software_security_code(
            self.config.software_id,
            self.config.software_pin,
            credit_note_data.number
        )

        return self._build_credit_note_xml(
            credit_note_data=credit_note_data,
            cude=cude,
            software_security_code=software_security_code,
            subtotal=subtotal,
            tax_iva=tax_iva,
            total=total
        )

    def _build_credit_note_xml(
        self,
        credit_note_data: CreditNoteData,
        cude: str,
        software_security_code: str,
        subtotal: float,
        tax_iva: float,
        total: float
    ) -> etree._Element:
        """Construir estructura XML de nota credito."""

        nsmap = {
            None: NS['nc'],
            'cac': NS['cac'],
            'cbc': NS['cbc'],
            'ext': NS['ext'],
            'sts': NS['sts'],
            'xsi': NS['xsi'],
        }

        credit_note = etree.Element('CreditNote', nsmap=nsmap)

        # UBLExtensions
        self._add_ubl_extensions_cn(
            credit_note, credit_note_data, cude, software_security_code
        )

        # Elementos basicos
        self._add_basic_elements_cn(credit_note, credit_note_data, cude)

        # DiscrepancyResponse ANTES de BillingReference (orden segun Anexo Tecnico DIAN)
        self._add_discrepancy_response(credit_note, credit_note_data)

        # Referencia a factura
        self._add_billing_reference(credit_note, credit_note_data)

        # Proveedor
        self._add_supplier(credit_note, credit_note_data.supplier)

        # Cliente
        self._add_customer(credit_note, credit_note_data.customer)

        # Medios de pago
        self._add_payment_means(credit_note, credit_note_data)

        # Impuestos totales
        self._add_tax_total(credit_note, subtotal, tax_iva)

        # Totales monetarios
        self._add_monetary_total_cn(credit_note, subtotal, tax_iva, total)

        # Lineas
        self._add_credit_note_lines(credit_note, credit_note_data.lines)

        return credit_note

    def _add_ubl_extensions_cn(
        self,
        credit_note: etree._Element,
        credit_note_data: CreditNoteData,
        cude: str,
        software_security_code: str
    ):
        """Agregar UBLExtensions para nota credito."""
        # Usar el mismo metodo de factura pero sin InvoiceControl
        from .constants import SCHEME_AGENCY_ATTRS, COUNTRY_ID_ATTRS, AUTHORIZATION_PROVIDER_ID
        from ..client.dian_simple import calcular_dv

        extensions = etree.SubElement(credit_note, '{%s}UBLExtensions' % NS['ext'])

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

    def _add_basic_elements_cn(
        self,
        credit_note: etree._Element,
        credit_note_data: CreditNoteData,
        cude: str
    ):
        """Agregar elementos basicos de nota credito."""
        from .constants import DIAN_UBL_VERSION

        etree.SubElement(credit_note, '{%s}UBLVersionID' % NS['cbc']).text = DIAN_UBL_VERSION
        # CustomizationID para notas credito es 20
        etree.SubElement(credit_note, '{%s}CustomizationID' % NS['cbc']).text = CUSTOMIZATION_ID_CREDIT_NOTE
        etree.SubElement(credit_note, '{%s}ProfileID' % NS['cbc']).text = DIAN_PROFILE_ID_CREDIT_NOTE
        etree.SubElement(
            credit_note, '{%s}ProfileExecutionID' % NS['cbc']
        ).text = self.config.environment
        etree.SubElement(credit_note, '{%s}ID' % NS['cbc']).text = credit_note_data.number

        uuid_el = etree.SubElement(credit_note, '{%s}UUID' % NS['cbc'])
        uuid_el.set('schemeID', self.config.environment)
        uuid_el.set('schemeName', 'CUDE-SHA384')
        uuid_el.text = cude

        etree.SubElement(credit_note, '{%s}IssueDate' % NS['cbc']).text = credit_note_data.issue_date
        etree.SubElement(credit_note, '{%s}IssueTime' % NS['cbc']).text = credit_note_data.issue_time

        cn_type = etree.SubElement(credit_note, '{%s}CreditNoteTypeCode' % NS['cbc'])
        cn_type.text = '91'

        etree.SubElement(credit_note, '{%s}Note' % NS['cbc']).text = credit_note_data.note

        doc_currency = etree.SubElement(credit_note, '{%s}DocumentCurrencyCode' % NS['cbc'])
        doc_currency.set('listAgencyID', '6')
        doc_currency.set('listAgencyName', 'United Nations Economic Commission for Europe')
        doc_currency.set('listID', 'ISO 4217 Alpha')
        doc_currency.text = 'COP'

        etree.SubElement(
            credit_note, '{%s}LineCountNumeric' % NS['cbc']
        ).text = str(len(credit_note_data.lines))

    def _add_billing_reference(
        self,
        credit_note: etree._Element,
        credit_note_data: CreditNoteData
    ):
        """Agregar referencia a factura original."""
        billing_ref = etree.SubElement(credit_note, '{%s}BillingReference' % NS['cac'])
        inv_doc_ref = etree.SubElement(billing_ref, '{%s}InvoiceDocumentReference' % NS['cac'])
        etree.SubElement(
            inv_doc_ref, '{%s}ID' % NS['cbc']
        ).text = credit_note_data.billing_reference_id

        uuid_ref = etree.SubElement(inv_doc_ref, '{%s}UUID' % NS['cbc'])
        uuid_ref.set('schemeName', 'CUFE-SHA384')
        uuid_ref.text = credit_note_data.billing_reference_uuid

        etree.SubElement(
            inv_doc_ref, '{%s}IssueDate' % NS['cbc']
        ).text = credit_note_data.billing_reference_date

    def _add_discrepancy_response(
        self,
        credit_note: etree._Element,
        credit_note_data: CreditNoteData
    ):
        """
        Agregar respuesta de discrepancia.

        El DiscrepancyResponse es REQUERIDO para notas credito y contiene:
        - ReferenceID: Numero de factura referenciada
        - ResponseCode: Codigo del motivo (1-5)
        - Description: Descripcion del motivo
        """
        disc_resp = etree.SubElement(credit_note, '{%s}DiscrepancyResponse' % NS['cac'])
        etree.SubElement(
            disc_resp, '{%s}ReferenceID' % NS['cbc']
        ).text = credit_note_data.billing_reference_id
        etree.SubElement(
            disc_resp, '{%s}ResponseCode' % NS['cbc']
        ).text = credit_note_data.discrepancy_response_code
        etree.SubElement(
            disc_resp, '{%s}Description' % NS['cbc']
        ).text = credit_note_data.response_description

    def _add_monetary_total_cn(
        self,
        credit_note: etree._Element,
        subtotal: float,
        tax_iva: float,
        total: float
    ):
        """Agregar totales monetarios para nota credito."""
        monetary = etree.SubElement(credit_note, '{%s}LegalMonetaryTotal' % NS['cac'])

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

    def _add_credit_note_lines(
        self,
        credit_note: etree._Element,
        lines: List[InvoiceLine]
    ):
        """Agregar lineas de nota credito."""
        for idx, line_data in enumerate(lines, 1):
            line_total = line_data.quantity * line_data.unit_price
            line_tax = line_total * (line_data.tax_percent / 100)

            line = etree.SubElement(credit_note, '{%s}CreditNoteLine' % NS['cac'])
            etree.SubElement(line, '{%s}ID' % NS['cbc']).text = str(idx)

            qty = etree.SubElement(line, '{%s}CreditedQuantity' % NS['cbc'])
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
