# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constructor de facturas UBL 2.1 para DIAN Colombia.
Basado en implementacion funcional aprobada por DIAN.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from lxml import etree

from .constants import (
    NS,
    SCHEME_AGENCY_ATTRS,
    DIAN_UBL_VERSION,
    DIAN_CUSTOMIZATION_ID,
    DIAN_PROFILE_ID,
    COUNTRY_ID_ATTRS,
    AUTHORIZATION_PROVIDER_ID,
)
from ..client.dian_simple import calcular_dv


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
    """Linea de factura."""
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
    # Software DIAN
    software_id: str
    software_pin: str
    technical_key: str
    test_set_id: str = ''

    # Empresa
    nit: str
    company_name: str

    # Resolucion
    resolution_number: str
    resolution_date: str
    resolution_end_date: str
    prefix: str
    range_from: str
    range_to: str

    # Ambiente
    environment: str = '2'  # '1'=Produccion, '2'=Pruebas


@dataclass
class InvoiceData:
    """Datos de factura."""
    number: str
    issue_date: str
    issue_time: str
    due_date: str = None
    note: str = 'Factura electronica'
    supplier: Party = None
    customer: Party = None
    lines: List[InvoiceLine] = field(default_factory=list)


# =============================================================================
# BUILDER
# =============================================================================

class InvoiceBuilder:
    """
    Constructor de facturas electronicas UBL 2.1 para DIAN.

    Genera XML valido segun Anexo Tecnico v1.9.
    """

    def __init__(self, config: InvoiceConfig):
        """
        Inicializar builder.

        Args:
            config: Configuracion de factura
        """
        self.config = config

    def build(self, invoice_data: InvoiceData) -> etree._Element:
        """
        Construir factura XML.

        Args:
            invoice_data: Datos de la factura

        Returns:
            Elemento XML de la factura
        """
        # Calcular totales
        subtotal = sum(
            line.quantity * line.unit_price
            for line in invoice_data.lines
        )
        tax_iva = sum(
            line.quantity * line.unit_price * (line.tax_percent / 100)
            for line in invoice_data.lines
        )
        total = subtotal + tax_iva

        # Calcular CUFE y SoftwareSecurityCode
        from ..client.dian_simple import calcular_cufe, calcular_software_security_code

        cufe = calcular_cufe(
            numero=invoice_data.number,
            fecha_emision=invoice_data.issue_date,
            hora_emision=invoice_data.issue_time,
            subtotal=subtotal,
            iva=tax_iva,
            total=total,
            nit_emisor=self.config.nit,
            nit_adquiriente=invoice_data.customer.nit,
            clave_tecnica=self.config.technical_key,
            tipo_ambiente=self.config.environment
        )

        software_security_code = calcular_software_security_code(
            self.config.software_id,
            self.config.software_pin,
            invoice_data.number
        )

        # Construir XML
        return self._build_invoice_xml(
            invoice_data=invoice_data,
            cufe=cufe,
            software_security_code=software_security_code,
            subtotal=subtotal,
            tax_iva=tax_iva,
            total=total
        )

    def _build_invoice_xml(
        self,
        invoice_data: InvoiceData,
        cufe: str,
        software_security_code: str,
        subtotal: float,
        tax_iva: float,
        total: float
    ) -> etree._Element:
        """Construir estructura XML de factura."""

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
        self._add_ubl_extensions(
            invoice, invoice_data, cufe, software_security_code
        )

        # Elementos basicos
        self._add_basic_elements(invoice, invoice_data, cufe)

        # Proveedor
        self._add_supplier(invoice, invoice_data.supplier)

        # Cliente
        self._add_customer(invoice, invoice_data.customer)

        # Medios de pago
        self._add_payment_means(invoice, invoice_data)

        # Impuestos totales
        self._add_tax_total(invoice, subtotal, tax_iva)

        # Totales monetarios
        self._add_monetary_total(invoice, subtotal, tax_iva, total)

        # Lineas de factura
        self._add_invoice_lines(invoice, invoice_data.lines)

        return invoice

    def _add_ubl_extensions(
        self,
        invoice: etree._Element,
        invoice_data: InvoiceData,
        cufe: str,
        software_security_code: str
    ):
        """Agregar UBLExtensions con extensiones DIAN."""

        extensions = etree.SubElement(invoice, '{%s}UBLExtensions' % NS['ext'])

        # Extension 1: DIAN Extensions
        ext1 = etree.SubElement(extensions, '{%s}UBLExtension' % NS['ext'])
        ext1_content = etree.SubElement(ext1, '{%s}ExtensionContent' % NS['ext'])

        dian_ext = etree.SubElement(
            ext1_content,
            '{%s}DianExtensions' % NS['sts'],
            nsmap={'sts': NS['sts']}
        )

        # InvoiceControl
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
        qr_code.text = f"{qr_base}/document/searchqr?documentkey={cufe}"

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
        invoice: etree._Element,
        invoice_data: InvoiceData,
        cufe: str
    ):
        """Agregar elementos basicos de factura."""

        etree.SubElement(invoice, '{%s}UBLVersionID' % NS['cbc']).text = DIAN_UBL_VERSION
        etree.SubElement(invoice, '{%s}CustomizationID' % NS['cbc']).text = DIAN_CUSTOMIZATION_ID
        etree.SubElement(invoice, '{%s}ProfileID' % NS['cbc']).text = DIAN_PROFILE_ID
        etree.SubElement(
            invoice, '{%s}ProfileExecutionID' % NS['cbc']
        ).text = self.config.environment
        etree.SubElement(invoice, '{%s}ID' % NS['cbc']).text = invoice_data.number

        uuid_el = etree.SubElement(invoice, '{%s}UUID' % NS['cbc'])
        uuid_el.set('schemeID', self.config.environment)
        uuid_el.set('schemeName', 'CUFE-SHA384')
        uuid_el.text = cufe

        etree.SubElement(invoice, '{%s}IssueDate' % NS['cbc']).text = invoice_data.issue_date
        etree.SubElement(invoice, '{%s}IssueTime' % NS['cbc']).text = invoice_data.issue_time
        if invoice_data.due_date:
            etree.SubElement(invoice, '{%s}DueDate' % NS['cbc']).text = invoice_data.due_date

        inv_type = etree.SubElement(invoice, '{%s}InvoiceTypeCode' % NS['cbc'])
        inv_type.text = '01'

        etree.SubElement(invoice, '{%s}Note' % NS['cbc']).text = invoice_data.note

        doc_currency = etree.SubElement(invoice, '{%s}DocumentCurrencyCode' % NS['cbc'])
        doc_currency.set('listAgencyID', '6')
        doc_currency.set('listAgencyName', 'United Nations Economic Commission for Europe')
        doc_currency.set('listID', 'ISO 4217 Alpha')
        doc_currency.text = 'COP'

        etree.SubElement(
            invoice, '{%s}LineCountNumeric' % NS['cbc']
        ).text = str(len(invoice_data.lines))

    def _add_supplier(self, invoice: etree._Element, supplier: Party):
        """Agregar proveedor."""
        supplier_el = etree.SubElement(invoice, '{%s}AccountingSupplierParty' % NS['cac'])
        etree.SubElement(supplier_el, '{%s}AdditionalAccountID' % NS['cbc']).text = supplier.organization_code

        party = etree.SubElement(supplier_el, '{%s}Party' % NS['cac'])

        # PartyName
        party_name = etree.SubElement(party, '{%s}PartyName' % NS['cac'])
        etree.SubElement(party_name, '{%s}Name' % NS['cbc']).text = supplier.name

        # PhysicalLocation
        if supplier.address:
            self._add_address(party, supplier.address, '{%s}PhysicalLocation' % NS['cac'])

        # PartyTaxScheme
        self._add_party_tax_scheme(party, supplier)

        # PartyLegalEntity
        self._add_party_legal_entity(party, supplier)

        # Contact
        if supplier.email:
            contact = etree.SubElement(party, '{%s}Contact' % NS['cac'])
            etree.SubElement(contact, '{%s}ElectronicMail' % NS['cbc']).text = supplier.email

    def _add_customer(self, invoice: etree._Element, customer: Party):
        """Agregar cliente."""
        customer_el = etree.SubElement(invoice, '{%s}AccountingCustomerParty' % NS['cac'])
        etree.SubElement(customer_el, '{%s}AdditionalAccountID' % NS['cbc']).text = customer.organization_code

        party = etree.SubElement(customer_el, '{%s}Party' % NS['cac'])

        # PartyIdentification (obligatorio cuando AdditionalAccountID = '2')
        party_ident = etree.SubElement(party, '{%s}PartyIdentification' % NS['cac'])
        party_ident_id = etree.SubElement(party_ident, '{%s}ID' % NS['cbc'])
        party_ident_id.set('schemeAgencyID', '195')
        party_ident_id.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        party_ident_id.set('schemeName', customer.scheme_name)
        party_ident_id.text = customer.nit

        # PartyName
        party_name = etree.SubElement(party, '{%s}PartyName' % NS['cac'])
        etree.SubElement(party_name, '{%s}Name' % NS['cbc']).text = customer.name

        # PhysicalLocation
        if customer.address:
            self._add_address(party, customer.address, '{%s}PhysicalLocation' % NS['cac'])

        # PartyTaxScheme
        self._add_party_tax_scheme(party, customer)

        # PartyLegalEntity
        self._add_party_legal_entity(party, customer)

        # Contact
        if customer.email:
            contact = etree.SubElement(party, '{%s}Contact' % NS['cac'])
            etree.SubElement(contact, '{%s}ElectronicMail' % NS['cbc']).text = customer.email

    def _add_address(self, parent: etree._Element, address: Address, container_tag: str):
        """Agregar direccion."""
        container = etree.SubElement(parent, container_tag)
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
        """Agregar esquema de impuestos de la parte."""
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

        # RegistrationAddress
        if party_data.address:
            reg_addr = etree.SubElement(tax_scheme_el, '{%s}RegistrationAddress' % NS['cac'])
            etree.SubElement(reg_addr, '{%s}ID' % NS['cbc']).text = party_data.address.city_code
            etree.SubElement(reg_addr, '{%s}CityName' % NS['cbc']).text = party_data.address.city_name
            etree.SubElement(reg_addr, '{%s}PostalZone' % NS['cbc']).text = party_data.address.postal_zone
            etree.SubElement(
                reg_addr, '{%s}CountrySubentity' % NS['cbc']
            ).text = party_data.address.country_subentity
            etree.SubElement(
                reg_addr, '{%s}CountrySubentityCode' % NS['cbc']
            ).text = party_data.address.country_subentity_code
            reg_line = etree.SubElement(reg_addr, '{%s}AddressLine' % NS['cac'])
            etree.SubElement(reg_line, '{%s}Line' % NS['cbc']).text = party_data.address.address_line
            reg_country = etree.SubElement(reg_addr, '{%s}Country' % NS['cac'])
            etree.SubElement(
                reg_country, '{%s}IdentificationCode' % NS['cbc']
            ).text = party_data.address.country_code
            reg_country_name = etree.SubElement(reg_country, '{%s}Name' % NS['cbc'])
            reg_country_name.set('languageID', 'es')
            reg_country_name.text = party_data.address.country_name

        # TaxScheme
        ts = etree.SubElement(tax_scheme_el, '{%s}TaxScheme' % NS['cac'])
        etree.SubElement(ts, '{%s}ID' % NS['cbc']).text = party_data.tax_scheme_code
        etree.SubElement(ts, '{%s}Name' % NS['cbc']).text = party_data.tax_scheme_name

    def _add_party_legal_entity(self, party: etree._Element, party_data: Party):
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

        # CorporateRegistrationScheme (solo para proveedor)
        if party_data.organization_code == '1':
            corp_reg = etree.SubElement(legal, '{%s}CorporateRegistrationScheme' % NS['cac'])
            etree.SubElement(corp_reg, '{%s}ID' % NS['cbc']).text = self.config.prefix
            etree.SubElement(corp_reg, '{%s}Name' % NS['cbc']).text = 'Punto de venta'

    def _add_payment_means(self, invoice: etree._Element, invoice_data: InvoiceData):
        """Agregar medios de pago."""
        payment = etree.SubElement(invoice, '{%s}PaymentMeans' % NS['cac'])
        etree.SubElement(payment, '{%s}ID' % NS['cbc']).text = '1'
        etree.SubElement(payment, '{%s}PaymentMeansCode' % NS['cbc']).text = '10'  # Efectivo
        etree.SubElement(
            payment, '{%s}PaymentDueDate' % NS['cbc']
        ).text = invoice_data.due_date or invoice_data.issue_date

    def _add_tax_total(self, invoice: etree._Element, subtotal: float, tax_iva: float):
        """Agregar totales de impuestos."""
        tax_total = etree.SubElement(invoice, '{%s}TaxTotal' % NS['cac'])
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
        invoice: etree._Element,
        subtotal: float,
        tax_iva: float,
        total: float
    ):
        """Agregar totales monetarios."""
        monetary = etree.SubElement(invoice, '{%s}LegalMonetaryTotal' % NS['cac'])

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
            el.set('currencyID', 'COP')
            el.text = f"{value:.2f}"

    def _add_invoice_lines(self, invoice: etree._Element, lines: List[InvoiceLine]):
        """Agregar lineas de factura."""
        for idx, line_data in enumerate(lines, 1):
            line_total = line_data.quantity * line_data.unit_price
            line_tax = line_total * (line_data.tax_percent / 100)

            line = etree.SubElement(invoice, '{%s}InvoiceLine' % NS['cac'])
            etree.SubElement(line, '{%s}ID' % NS['cbc']).text = str(idx)

            qty = etree.SubElement(line, '{%s}InvoicedQuantity' % NS['cbc'])
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
