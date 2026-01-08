# This file is part of dian_fe.
"""
Generadores XML UBL 2.1 para documentos DIAN Colombia.
Soporta: Facturas, Notas Credito, Notas Debito.
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from lxml import etree

from .config import (
    NS, SCHEME_AGENCY_ATTRS, COUNTRY_ID_ATTRS,
    DIAN_UBL_VERSION, DIAN_PROFILE_ID, DIAN_PROFILE_ID_CREDIT_NOTE,
    DIAN_PROFILE_ID_DEBIT_NOTE, AUTHORIZATION_PROVIDER_ID,
    CUSTOMIZATION_ID_INVOICE, CUSTOMIZATION_ID_CREDIT_NOTE,
    CUSTOMIZATION_ID_DEBIT_NOTE, CREDIT_REASONS, DEBIT_REASONS
)
from .utils import (
    calcular_dv, calcular_cufe, calcular_cude,
    calcular_software_security_code
)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Address:
    """Direccion."""
    city_code: str
    city_name: str
    postal_zone: str
    country_subentity: str
    country_subentity_code: str
    address_line: str
    country_code: str = 'CO'
    country_name: str = 'Colombia'


@dataclass
class Party:
    """Parte (proveedor o cliente)."""
    nit: str
    name: str
    legal_name: str
    organization_code: str  # '1' = Persona Juridica, '2' = Persona Natural
    tax_level_code: str  # Ej: 'R-99-PN', 'O-07;O-09'
    tax_scheme_code: str = '01'  # IVA
    tax_scheme_name: str = 'IVA'
    scheme_name: str = '31'  # 31=NIT, 13=Cedula
    address: Address = None
    email: str = ''
    responsability_regime_code: str = '48'  # 48=IVA, 49=No IVA


@dataclass
class InvoiceLine:
    """Linea de documento."""
    description: str
    quantity: float
    unit_code: str
    unit_price: float
    tax_percent: float = 19.0
    item_id: str = ''
    item_scheme_id: str = '999'
    item_scheme_name: str = 'Estandar de adopcion del contribuyente'


@dataclass
class InvoiceConfig:
    """Configuracion de factura."""
    software_id: str
    software_pin: str
    technical_key: str
    nit: str
    company_name: str
    resolution_number: str
    resolution_date: str
    resolution_end_date: str
    prefix: str
    range_from: str
    range_to: str
    test_set_id: str = ''
    environment: str = '2'  # '1'=Produccion, '2'=Pruebas


# =============================================================================
# INVOICE BUILDER
# =============================================================================

class InvoiceBuilder:
    """Constructor de facturas electronicas UBL 2.1 para DIAN."""

    def __init__(self, config: InvoiceConfig):
        self.config = config

    def build(
        self,
        number: str,
        issue_date: str,
        issue_time: str,
        supplier: Party,
        customer: Party,
        lines: List[InvoiceLine],
        note: str = 'Factura electronica',
        due_date: str = None
    ) -> etree._Element:
        """Construir factura XML."""
        # Calcular totales
        subtotal = sum(l.quantity * l.unit_price for l in lines)
        tax_iva = sum(l.quantity * l.unit_price * (l.tax_percent / 100) for l in lines)
        total = subtotal + tax_iva

        # Calcular CUFE
        cufe = calcular_cufe(
            numero=number,
            fecha_emision=issue_date,
            hora_emision=issue_time,
            subtotal=subtotal,
            iva=tax_iva,
            total=total,
            nit_emisor=self.config.nit,
            nit_adquiriente=customer.nit,
            clave_tecnica=self.config.technical_key,
            tipo_ambiente=self.config.environment
        )

        software_security_code = calcular_software_security_code(
            self.config.software_id,
            self.config.software_pin,
            number
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

        invoice = etree.Element('Invoice', nsmap=nsmap)

        # UBLExtensions
        self._add_ubl_extensions(invoice, cufe, software_security_code, True)

        # Elementos basicos
        self._add_basic_elements(
            invoice, number, issue_date, issue_time, cufe,
            CUSTOMIZATION_ID_INVOICE, DIAN_PROFILE_ID,
            'InvoiceTypeCode', '01', note, len(lines), due_date
        )

        # Partes
        self._add_supplier(invoice, supplier)
        self._add_customer(invoice, customer)

        # Pago
        self._add_payment_means(invoice, due_date or issue_date)

        # Impuestos y totales
        self._add_tax_total(invoice, subtotal, tax_iva)
        self._add_monetary_total(invoice, subtotal, tax_iva, total, 'LegalMonetaryTotal')

        # Lineas
        self._add_lines(invoice, lines, 'InvoiceLine', 'InvoicedQuantity')

        return invoice

    def _add_ubl_extensions(
        self,
        doc: etree._Element,
        uuid_value: str,
        software_security_code: str,
        include_invoice_control: bool
    ):
        """Agregar UBLExtensions."""
        extensions = etree.SubElement(doc, '{%s}UBLExtensions' % NS['ext'])

        ext1 = etree.SubElement(extensions, '{%s}UBLExtension' % NS['ext'])
        ext1_content = etree.SubElement(ext1, '{%s}ExtensionContent' % NS['ext'])

        dian_ext = etree.SubElement(
            ext1_content,
            '{%s}DianExtensions' % NS['sts'],
            nsmap={'sts': NS['sts']}
        )

        # InvoiceControl (solo para facturas)
        if include_invoice_control:
            self._add_invoice_control(dian_ext)

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
        qr_code.text = f"{qr_base}/document/searchqr?documentkey={uuid_value}"

        # Extension 2: Signature (vacio, se llena con firma)
        ext2 = etree.SubElement(extensions, '{%s}UBLExtension' % NS['ext'])
        etree.SubElement(ext2, '{%s}ExtensionContent' % NS['ext'])

    def _add_invoice_control(self, dian_ext: etree._Element):
        """Agregar InvoiceControl."""
        inv_control = etree.SubElement(dian_ext, '{%s}InvoiceControl' % NS['sts'])
        etree.SubElement(
            inv_control, '{%s}InvoiceAuthorization' % NS['sts']
        ).text = self.config.resolution_number

        auth_period = etree.SubElement(inv_control, '{%s}AuthorizationPeriod' % NS['sts'])
        etree.SubElement(auth_period, '{%s}StartDate' % NS['cbc']).text = self.config.resolution_date
        etree.SubElement(auth_period, '{%s}EndDate' % NS['cbc']).text = self.config.resolution_end_date

        auth_inv = etree.SubElement(inv_control, '{%s}AuthorizedInvoices' % NS['sts'])
        etree.SubElement(auth_inv, '{%s}Prefix' % NS['sts']).text = self.config.prefix
        etree.SubElement(auth_inv, '{%s}From' % NS['sts']).text = self.config.range_from
        etree.SubElement(auth_inv, '{%s}To' % NS['sts']).text = self.config.range_to

    def _add_basic_elements(
        self,
        doc: etree._Element,
        number: str,
        issue_date: str,
        issue_time: str,
        uuid_value: str,
        customization_id: str,
        profile_id: str,
        type_code_tag: str,
        type_code: str,
        note: str,
        line_count: int,
        due_date: str = None
    ):
        """Agregar elementos basicos."""
        etree.SubElement(doc, '{%s}UBLVersionID' % NS['cbc']).text = DIAN_UBL_VERSION
        etree.SubElement(doc, '{%s}CustomizationID' % NS['cbc']).text = customization_id
        etree.SubElement(doc, '{%s}ProfileID' % NS['cbc']).text = profile_id
        etree.SubElement(doc, '{%s}ProfileExecutionID' % NS['cbc']).text = self.config.environment
        etree.SubElement(doc, '{%s}ID' % NS['cbc']).text = number

        uuid_scheme = 'CUFE-SHA384' if customization_id == CUSTOMIZATION_ID_INVOICE else 'CUDE-SHA384'
        uuid_el = etree.SubElement(doc, '{%s}UUID' % NS['cbc'])
        uuid_el.set('schemeID', self.config.environment)
        uuid_el.set('schemeName', uuid_scheme)
        uuid_el.text = uuid_value

        etree.SubElement(doc, '{%s}IssueDate' % NS['cbc']).text = issue_date
        etree.SubElement(doc, '{%s}IssueTime' % NS['cbc']).text = issue_time

        if due_date and type_code_tag == 'InvoiceTypeCode':
            etree.SubElement(doc, '{%s}DueDate' % NS['cbc']).text = due_date

        type_el = etree.SubElement(doc, '{%s}%s' % (NS['cbc'], type_code_tag))
        type_el.text = type_code

        etree.SubElement(doc, '{%s}Note' % NS['cbc']).text = note

        doc_currency = etree.SubElement(doc, '{%s}DocumentCurrencyCode' % NS['cbc'])
        doc_currency.set('listAgencyID', '6')
        doc_currency.set('listAgencyName', 'United Nations Economic Commission for Europe')
        doc_currency.set('listID', 'ISO 4217 Alpha')
        doc_currency.text = 'COP'

        etree.SubElement(doc, '{%s}LineCountNumeric' % NS['cbc']).text = str(line_count)

    def _add_supplier(self, doc: etree._Element, supplier: Party):
        """Agregar proveedor."""
        supplier_el = etree.SubElement(doc, '{%s}AccountingSupplierParty' % NS['cac'])
        etree.SubElement(supplier_el, '{%s}AdditionalAccountID' % NS['cbc']).text = supplier.organization_code

        party = etree.SubElement(supplier_el, '{%s}Party' % NS['cac'])

        party_name = etree.SubElement(party, '{%s}PartyName' % NS['cac'])
        etree.SubElement(party_name, '{%s}Name' % NS['cbc']).text = supplier.name

        if supplier.address:
            self._add_address(party, supplier.address, 'PhysicalLocation')

        self._add_party_tax_scheme(party, supplier)
        self._add_party_legal_entity(party, supplier)

        if supplier.email:
            contact = etree.SubElement(party, '{%s}Contact' % NS['cac'])
            etree.SubElement(contact, '{%s}ElectronicMail' % NS['cbc']).text = supplier.email

    def _add_customer(self, doc: etree._Element, customer: Party):
        """Agregar cliente."""
        customer_el = etree.SubElement(doc, '{%s}AccountingCustomerParty' % NS['cac'])
        etree.SubElement(customer_el, '{%s}AdditionalAccountID' % NS['cbc']).text = customer.organization_code

        party = etree.SubElement(customer_el, '{%s}Party' % NS['cac'])

        party_ident = etree.SubElement(party, '{%s}PartyIdentification' % NS['cac'])
        party_ident_id = etree.SubElement(party_ident, '{%s}ID' % NS['cbc'])
        party_ident_id.set('schemeAgencyID', '195')
        party_ident_id.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        party_ident_id.set('schemeName', customer.scheme_name)
        party_ident_id.text = customer.nit

        party_name = etree.SubElement(party, '{%s}PartyName' % NS['cac'])
        etree.SubElement(party_name, '{%s}Name' % NS['cbc']).text = customer.name

        if customer.address:
            self._add_address(party, customer.address, 'PhysicalLocation')

        self._add_party_tax_scheme(party, customer)
        self._add_party_legal_entity(party, customer, include_corp_reg=False)

        if customer.email:
            contact = etree.SubElement(party, '{%s}Contact' % NS['cac'])
            etree.SubElement(contact, '{%s}ElectronicMail' % NS['cbc']).text = customer.email

    def _add_address(self, parent: etree._Element, address: Address, container_name: str):
        """Agregar direccion."""
        container = etree.SubElement(parent, '{%s}%s' % (NS['cac'], container_name))
        addr = etree.SubElement(container, '{%s}Address' % NS['cac'])
        etree.SubElement(addr, '{%s}ID' % NS['cbc']).text = address.city_code
        etree.SubElement(addr, '{%s}CityName' % NS['cbc']).text = address.city_name
        etree.SubElement(addr, '{%s}PostalZone' % NS['cbc']).text = address.postal_zone
        etree.SubElement(addr, '{%s}CountrySubentity' % NS['cbc']).text = address.country_subentity
        etree.SubElement(addr, '{%s}CountrySubentityCode' % NS['cbc']).text = address.country_subentity_code
        addr_line = etree.SubElement(addr, '{%s}AddressLine' % NS['cac'])
        etree.SubElement(addr_line, '{%s}Line' % NS['cbc']).text = address.address_line
        country = etree.SubElement(addr, '{%s}Country' % NS['cac'])
        etree.SubElement(country, '{%s}IdentificationCode' % NS['cbc']).text = address.country_code
        country_name = etree.SubElement(country, '{%s}Name' % NS['cbc'])
        country_name.set('languageID', 'es')
        country_name.text = address.country_name

    def _add_party_tax_scheme(self, party: etree._Element, party_data: Party):
        """Agregar esquema de impuestos."""
        dv = str(calcular_dv(party_data.nit))

        tax_scheme_el = etree.SubElement(party, '{%s}PartyTaxScheme' % NS['cac'])
        etree.SubElement(tax_scheme_el, '{%s}RegistrationName' % NS['cbc']).text = party_data.legal_name

        comp_id = etree.SubElement(tax_scheme_el, '{%s}CompanyID' % NS['cbc'])
        comp_id.set('schemeAgencyID', '195')
        comp_id.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        comp_id.set('schemeID', dv)
        comp_id.set('schemeName', party_data.scheme_name)
        comp_id.text = party_data.nit

        tax_level = etree.SubElement(tax_scheme_el, '{%s}TaxLevelCode' % NS['cbc'])
        tax_level.set('listName', party_data.responsability_regime_code)
        tax_level.text = party_data.tax_level_code

        if party_data.address:
            self._add_registration_address(tax_scheme_el, party_data.address)

        ts = etree.SubElement(tax_scheme_el, '{%s}TaxScheme' % NS['cac'])
        etree.SubElement(ts, '{%s}ID' % NS['cbc']).text = party_data.tax_scheme_code
        etree.SubElement(ts, '{%s}Name' % NS['cbc']).text = party_data.tax_scheme_name

    def _add_registration_address(self, tax_scheme_el: etree._Element, address: Address):
        """Agregar RegistrationAddress."""
        reg_addr = etree.SubElement(tax_scheme_el, '{%s}RegistrationAddress' % NS['cac'])
        etree.SubElement(reg_addr, '{%s}ID' % NS['cbc']).text = address.city_code
        etree.SubElement(reg_addr, '{%s}CityName' % NS['cbc']).text = address.city_name
        etree.SubElement(reg_addr, '{%s}PostalZone' % NS['cbc']).text = address.postal_zone
        etree.SubElement(reg_addr, '{%s}CountrySubentity' % NS['cbc']).text = address.country_subentity
        etree.SubElement(reg_addr, '{%s}CountrySubentityCode' % NS['cbc']).text = address.country_subentity_code
        reg_line = etree.SubElement(reg_addr, '{%s}AddressLine' % NS['cac'])
        etree.SubElement(reg_line, '{%s}Line' % NS['cbc']).text = address.address_line
        reg_country = etree.SubElement(reg_addr, '{%s}Country' % NS['cac'])
        etree.SubElement(reg_country, '{%s}IdentificationCode' % NS['cbc']).text = address.country_code
        reg_country_name = etree.SubElement(reg_country, '{%s}Name' % NS['cbc'])
        reg_country_name.set('languageID', 'es')
        reg_country_name.text = address.country_name

    def _add_party_legal_entity(self, party: etree._Element, party_data: Party, include_corp_reg: bool = True):
        """Agregar entidad legal."""
        dv = str(calcular_dv(party_data.nit))

        legal = etree.SubElement(party, '{%s}PartyLegalEntity' % NS['cac'])
        etree.SubElement(legal, '{%s}RegistrationName' % NS['cbc']).text = party_data.legal_name

        legal_id = etree.SubElement(legal, '{%s}CompanyID' % NS['cbc'])
        legal_id.set('schemeAgencyID', '195')
        legal_id.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        legal_id.set('schemeID', dv)
        legal_id.set('schemeName', party_data.scheme_name)
        legal_id.text = party_data.nit

        if include_corp_reg and party_data.organization_code == '1':
            corp_reg = etree.SubElement(legal, '{%s}CorporateRegistrationScheme' % NS['cac'])
            etree.SubElement(corp_reg, '{%s}ID' % NS['cbc']).text = self.config.prefix
            etree.SubElement(corp_reg, '{%s}Name' % NS['cbc']).text = 'Punto de venta'

    def _add_payment_means(self, doc: etree._Element, due_date: str):
        """Agregar medios de pago."""
        payment = etree.SubElement(doc, '{%s}PaymentMeans' % NS['cac'])
        etree.SubElement(payment, '{%s}ID' % NS['cbc']).text = '1'
        etree.SubElement(payment, '{%s}PaymentMeansCode' % NS['cbc']).text = '10'
        etree.SubElement(payment, '{%s}PaymentDueDate' % NS['cbc']).text = due_date

    def _add_tax_total(self, doc: etree._Element, subtotal: float, tax_iva: float):
        """Agregar totales de impuestos."""
        tax_total = etree.SubElement(doc, '{%s}TaxTotal' % NS['cac'])
        tax_amt = etree.SubElement(tax_total, '{%s}TaxAmount' % NS['cbc'])
        tax_amt.set('currencyID', 'COP')
        tax_amt.text = f"{tax_iva:.2f}"

        rounding = etree.SubElement(tax_total, '{%s}RoundingAmount' % NS['cbc'])
        rounding.set('currencyID', 'COP')
        rounding.text = '0.00'

        tax_sub = etree.SubElement(tax_total, '{%s}TaxSubtotal' % NS['cac'])
        taxable = etree.SubElement(tax_sub, '{%s}TaxableAmount' % NS['cbc'])
        taxable.set('currencyID', 'COP')
        taxable.text = f"{subtotal:.2f}"

        tax_amt2 = etree.SubElement(tax_sub, '{%s}TaxAmount' % NS['cbc'])
        tax_amt2.set('currencyID', 'COP')
        tax_amt2.text = f"{tax_iva:.2f}"

        tax_cat = etree.SubElement(tax_sub, '{%s}TaxCategory' % NS['cac'])
        etree.SubElement(tax_cat, '{%s}Percent' % NS['cbc']).text = '19.00'
        tax_sch = etree.SubElement(tax_cat, '{%s}TaxScheme' % NS['cac'])
        etree.SubElement(tax_sch, '{%s}ID' % NS['cbc']).text = '01'
        etree.SubElement(tax_sch, '{%s}Name' % NS['cbc']).text = 'IVA'

    def _add_monetary_total(
        self,
        doc: etree._Element,
        subtotal: float,
        tax_iva: float,
        total: float,
        tag_name: str
    ):
        """Agregar totales monetarios."""
        monetary = etree.SubElement(doc, '{%s}%s' % (NS['cac'], tag_name))

        tags = [
            ('LineExtensionAmount', subtotal),
            ('TaxExclusiveAmount', subtotal),
            ('TaxInclusiveAmount', total),
            ('AllowanceTotalAmount', 0),
            ('ChargeTotalAmount', 0),
        ]
        if tag_name == 'LegalMonetaryTotal':
            tags.append(('PrepaidAmount', 0))
        tags.append(('PayableAmount', total))

        for tag, value in tags:
            el = etree.SubElement(monetary, '{%s}%s' % (NS['cbc'], tag))
            el.set('currencyID', 'COP')
            el.text = f"{value:.2f}"

    def _add_lines(
        self,
        doc: etree._Element,
        lines: List[InvoiceLine],
        line_tag: str,
        qty_tag: str
    ):
        """Agregar lineas de documento."""
        for idx, line_data in enumerate(lines, 1):
            line_total = line_data.quantity * line_data.unit_price
            line_tax = line_total * (line_data.tax_percent / 100)

            line = etree.SubElement(doc, '{%s}%s' % (NS['cac'], line_tag))
            etree.SubElement(line, '{%s}ID' % NS['cbc']).text = str(idx)

            qty = etree.SubElement(line, '{%s}%s' % (NS['cbc'], qty_tag))
            qty.set('unitCode', line_data.unit_code)
            qty.text = f'{line_data.quantity:.2f}'

            line_ext = etree.SubElement(line, '{%s}LineExtensionAmount' % NS['cbc'])
            line_ext.set('currencyID', 'COP')
            line_ext.text = f"{line_total:.2f}"

            # TaxTotal de linea
            self._add_line_tax(line, line_total, line_tax, line_data.tax_percent)

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

    def _add_line_tax(
        self,
        line: etree._Element,
        line_total: float,
        line_tax: float,
        tax_percent: float
    ):
        """Agregar TaxTotal de linea."""
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
        etree.SubElement(line_tax_cat, '{%s}Percent' % NS['cbc']).text = f'{tax_percent:.2f}'
        line_tax_sch = etree.SubElement(line_tax_cat, '{%s}TaxScheme' % NS['cac'])
        etree.SubElement(line_tax_sch, '{%s}ID' % NS['cbc']).text = '01'
        etree.SubElement(line_tax_sch, '{%s}Name' % NS['cbc']).text = 'IVA'


# =============================================================================
# CREDIT NOTE BUILDER
# =============================================================================

class CreditNoteBuilder(InvoiceBuilder):
    """Constructor de notas credito electronicas UBL 2.1 para DIAN."""

    def build(
        self,
        number: str,
        issue_date: str,
        issue_time: str,
        supplier: Party,
        customer: Party,
        lines: List[InvoiceLine],
        billing_reference_id: str,
        billing_reference_uuid: str,
        billing_reference_date: str,
        discrepancy_response_code: str = '2',
        discrepancy_description: str = '',
        note: str = 'Nota credito'
    ) -> etree._Element:
        """Construir nota credito XML."""
        # Calcular totales
        subtotal = sum(l.quantity * l.unit_price for l in lines)
        tax_iva = sum(l.quantity * l.unit_price * (l.tax_percent / 100) for l in lines)
        total = subtotal + tax_iva

        # Calcular CUDE (no CUFE)
        cude = calcular_cude(
            numero=number,
            fecha_emision=issue_date,
            hora_emision=issue_time,
            subtotal=subtotal,
            iva=tax_iva,
            total=total,
            nit_emisor=self.config.nit,
            nit_adquiriente=customer.nit,
            software_pin=self.config.software_pin,
            tipo_ambiente=self.config.environment
        )

        software_security_code = calcular_software_security_code(
            self.config.software_id,
            self.config.software_pin,
            number
        )

        # Construir XML
        nsmap = {
            None: NS['nc'],
            'cac': NS['cac'],
            'cbc': NS['cbc'],
            'ext': NS['ext'],
            'sts': NS['sts'],
            'xsi': NS['xsi'],
        }

        credit_note = etree.Element('CreditNote', nsmap=nsmap)

        # UBLExtensions (sin InvoiceControl)
        self._add_ubl_extensions(credit_note, cude, software_security_code, False)

        # Elementos basicos
        self._add_basic_elements(
            credit_note, number, issue_date, issue_time, cude,
            CUSTOMIZATION_ID_CREDIT_NOTE, DIAN_PROFILE_ID_CREDIT_NOTE,
            'CreditNoteTypeCode', '91', note, len(lines)
        )

        # DiscrepancyResponse ANTES de BillingReference
        self._add_discrepancy_response(
            credit_note, billing_reference_id,
            discrepancy_response_code, discrepancy_description
        )

        # BillingReference
        self._add_billing_reference(
            credit_note, billing_reference_id,
            billing_reference_uuid, billing_reference_date
        )

        # Partes
        self._add_supplier(credit_note, supplier)
        self._add_customer(credit_note, customer)

        # Pago
        self._add_payment_means(credit_note, issue_date)

        # Impuestos y totales
        self._add_tax_total(credit_note, subtotal, tax_iva)
        self._add_monetary_total(credit_note, subtotal, tax_iva, total, 'LegalMonetaryTotal')

        # Lineas
        self._add_lines(credit_note, lines, 'CreditNoteLine', 'CreditedQuantity')

        return credit_note

    def _add_discrepancy_response(
        self,
        doc: etree._Element,
        reference_id: str,
        response_code: str,
        description: str
    ):
        """Agregar DiscrepancyResponse."""
        disc_resp = etree.SubElement(doc, '{%s}DiscrepancyResponse' % NS['cac'])
        etree.SubElement(disc_resp, '{%s}ReferenceID' % NS['cbc']).text = reference_id
        etree.SubElement(disc_resp, '{%s}ResponseCode' % NS['cbc']).text = response_code
        etree.SubElement(disc_resp, '{%s}Description' % NS['cbc']).text = \
            description or CREDIT_REASONS.get(response_code, 'Nota credito')

    def _add_billing_reference(
        self,
        doc: etree._Element,
        reference_id: str,
        reference_uuid: str,
        reference_date: str
    ):
        """Agregar BillingReference."""
        billing_ref = etree.SubElement(doc, '{%s}BillingReference' % NS['cac'])
        inv_doc_ref = etree.SubElement(billing_ref, '{%s}InvoiceDocumentReference' % NS['cac'])
        etree.SubElement(inv_doc_ref, '{%s}ID' % NS['cbc']).text = reference_id

        uuid_ref = etree.SubElement(inv_doc_ref, '{%s}UUID' % NS['cbc'])
        uuid_ref.set('schemeName', 'CUFE-SHA384')
        uuid_ref.text = reference_uuid

        etree.SubElement(inv_doc_ref, '{%s}IssueDate' % NS['cbc']).text = reference_date


# =============================================================================
# DEBIT NOTE BUILDER
# =============================================================================

class DebitNoteBuilder(InvoiceBuilder):
    """Constructor de notas debito electronicas UBL 2.1 para DIAN."""

    def build(
        self,
        number: str,
        issue_date: str,
        issue_time: str,
        supplier: Party,
        customer: Party,
        lines: List[InvoiceLine],
        billing_reference_id: str,
        billing_reference_uuid: str,
        billing_reference_date: str,
        discrepancy_response_code: str = '1',
        discrepancy_description: str = '',
        note: str = 'Nota debito'
    ) -> etree._Element:
        """Construir nota debito XML."""
        # Calcular totales
        subtotal = sum(l.quantity * l.unit_price for l in lines)
        tax_iva = sum(l.quantity * l.unit_price * (l.tax_percent / 100) for l in lines)
        total = subtotal + tax_iva

        # Calcular CUDE
        cude = calcular_cude(
            numero=number,
            fecha_emision=issue_date,
            hora_emision=issue_time,
            subtotal=subtotal,
            iva=tax_iva,
            total=total,
            nit_emisor=self.config.nit,
            nit_adquiriente=customer.nit,
            software_pin=self.config.software_pin,
            tipo_ambiente=self.config.environment
        )

        software_security_code = calcular_software_security_code(
            self.config.software_id,
            self.config.software_pin,
            number
        )

        # Construir XML
        nsmap = {
            None: NS['nd'],
            'cac': NS['cac'],
            'cbc': NS['cbc'],
            'ext': NS['ext'],
            'sts': NS['sts'],
            'xsi': NS['xsi'],
        }

        debit_note = etree.Element('DebitNote', nsmap=nsmap)

        # UBLExtensions (sin InvoiceControl)
        self._add_ubl_extensions(debit_note, cude, software_security_code, False)

        # Elementos basicos
        self._add_basic_elements(
            debit_note, number, issue_date, issue_time, cude,
            CUSTOMIZATION_ID_DEBIT_NOTE, DIAN_PROFILE_ID_DEBIT_NOTE,
            'DebitNoteTypeCode', '92', note, len(lines)
        )

        # DiscrepancyResponse
        self._add_discrepancy_response(
            debit_note, billing_reference_id,
            discrepancy_response_code, discrepancy_description
        )

        # BillingReference
        self._add_billing_reference(
            debit_note, billing_reference_id,
            billing_reference_uuid, billing_reference_date
        )

        # Partes
        self._add_supplier(debit_note, supplier)
        self._add_customer(debit_note, customer)

        # Pago
        self._add_payment_means(debit_note, issue_date)

        # Impuestos y totales
        self._add_tax_total(debit_note, subtotal, tax_iva)
        self._add_monetary_total(debit_note, subtotal, tax_iva, total, 'RequestedMonetaryTotal')

        # Lineas
        self._add_lines(debit_note, lines, 'DebitNoteLine', 'DebitedQuantity')

        return debit_note

    def _add_discrepancy_response(
        self,
        doc: etree._Element,
        reference_id: str,
        response_code: str,
        description: str
    ):
        """Agregar DiscrepancyResponse."""
        disc_resp = etree.SubElement(doc, '{%s}DiscrepancyResponse' % NS['cac'])
        etree.SubElement(disc_resp, '{%s}ReferenceID' % NS['cbc']).text = reference_id
        etree.SubElement(disc_resp, '{%s}ResponseCode' % NS['cbc']).text = response_code
        etree.SubElement(disc_resp, '{%s}Description' % NS['cbc']).text = \
            description or DEBIT_REASONS.get(response_code, 'Nota debito')

    def _add_billing_reference(
        self,
        doc: etree._Element,
        reference_id: str,
        reference_uuid: str,
        reference_date: str
    ):
        """Agregar BillingReference."""
        billing_ref = etree.SubElement(doc, '{%s}BillingReference' % NS['cac'])
        inv_doc_ref = etree.SubElement(billing_ref, '{%s}InvoiceDocumentReference' % NS['cac'])
        etree.SubElement(inv_doc_ref, '{%s}ID' % NS['cbc']).text = reference_id

        uuid_ref = etree.SubElement(inv_doc_ref, '{%s}UUID' % NS['cbc'])
        uuid_ref.set('schemeName', 'CUFE-SHA384')
        uuid_ref.text = reference_uuid

        etree.SubElement(inv_doc_ref, '{%s}IssueDate' % NS['cbc']).text = reference_date
