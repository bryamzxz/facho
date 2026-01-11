# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constructor de Documento Soporte (tipo 05) para DIAN Colombia.

El Documento Soporte se usa para compras a personas naturales
no obligadas a expedir factura.
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
    calcular_cude_flexible,
    calcular_software_security_code,
)


SUPPORT_DOCUMENT_TYPE_CODE = '05'
SUPPORT_DOCUMENT_PROFILE_ID = (
    'DIAN 2.1: documento soporte en adquisiciones efectuadas '
    'a no obligados a facturar'
)
SUPPORT_DOCUMENT_CUSTOMIZATION_ID = '05'


@dataclass
class SupportDocumentData:
    """
    Datos del documento soporte.

    Attributes:
        number: Numero del documento
        issue_date: Fecha de emision (YYYY-MM-DD)
        issue_time: Hora de emision (HH:MM:SS-05:00)
        due_date: Fecha de vencimiento (opcional)
        note: Nota del documento
        buyer: Quien compra y emite el documento
        seller: Quien vende (no obligado a facturar)
        lines: Lineas del documento
        payment_means_code: Codigo de medio de pago (default '10' = efectivo)
    """
    number: str
    issue_date: str
    issue_time: str
    due_date: str = None
    note: str = 'Documento soporte en adquisiciones'
    buyer: Party = None      # Quien compra y emite el documento
    seller: Party = None     # Quien vende (no obligado a facturar)
    lines: List[InvoiceLine] = field(default_factory=list)
    payment_means_code: str = '10'

    # Para compatibilidad con validador
    @property
    def supplier(self):
        """Alias para buyer (compatibilidad con validador)."""
        return self.buyer

    @property
    def customer(self):
        """Alias para seller (compatibilidad con validador)."""
        return self.seller


class SupportDocumentBuilder(InvoiceBuilder):
    """
    Constructor de Documento Soporte para DIAN.

    El Documento Soporte se utiliza cuando una empresa realiza
    compras a personas naturales que no estan obligadas a facturar.

    Example:
        config = InvoiceConfig(...)

        buyer = Party(nit='900123456', name='MI EMPRESA', ...)
        seller = Party(nit='12345678', scheme_name='13', ...)  # Cedula

        data = SupportDocumentData(
            number='DS0001',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
            buyer=buyer,
            seller=seller,
            lines=[InvoiceLine(..., taxes=[Tax.rete_fte(11.0, 100000)])]
        )

        builder = SupportDocumentBuilder(config)
        xml = builder.build(data)
    """

    def build(self, data: SupportDocumentData) -> etree._Element:
        """
        Construir XML de documento soporte.

        Args:
            data: Datos del documento soporte

        Returns:
            Elemento XML del documento
        """
        try:
            # Validar datos
            validate_before_build(data, self.config, "documento soporte")

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

            # Total documento
            total = truncar(subtotal + total_impuestos)

            # Calcular CUDE (documento soporte usa CUDE, no CUFE)
            cude = calcular_cude_flexible(
                numero=data.number,
                fecha_emision=data.issue_date,
                hora_emision=data.issue_time,
                subtotal=subtotal,
                impuestos=totales_impuestos,
                total=total,
                nit_emisor=self.config.nit,
                nit_adquiriente=data.seller.nit,
                software_pin=self.config.software_pin,
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
            self._add_ubl_extensions_support(
                doc, data, cude, software_security_code
            )

            # Campos principales
            etree.SubElement(
                doc, '{%s}UBLVersionID' % NS['cbc']
            ).text = DIAN_UBL_VERSION
            etree.SubElement(
                doc, '{%s}CustomizationID' % NS['cbc']
            ).text = SUPPORT_DOCUMENT_CUSTOMIZATION_ID
            etree.SubElement(
                doc, '{%s}ProfileID' % NS['cbc']
            ).text = SUPPORT_DOCUMENT_PROFILE_ID
            etree.SubElement(
                doc, '{%s}ProfileExecutionID' % NS['cbc']
            ).text = self.config.environment
            etree.SubElement(
                doc, '{%s}ID' % NS['cbc']
            ).text = data.number

            # UUID (CUDE)
            uuid_el = etree.SubElement(doc, '{%s}UUID' % NS['cbc'])
            uuid_el.set('schemeID', self.config.environment)
            uuid_el.set('schemeName', 'CUDE-SHA384')
            uuid_el.text = cude

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
            inv_type = etree.SubElement(doc, '{%s}InvoiceTypeCode' % NS['cbc'])
            inv_type.text = SUPPORT_DOCUMENT_TYPE_CODE

            # Nota
            if data.note:
                etree.SubElement(doc, '{%s}Note' % NS['cbc']).text = data.note

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

            # Partes (buyer es el emisor, seller es el proveedor)
            self._add_supplier(doc, data.buyer)
            self._add_customer(doc, data.seller)

            # Medio de pago
            payment = etree.SubElement(doc, '{%s}PaymentMeans' % NS['cac'])
            etree.SubElement(payment, '{%s}ID' % NS['cbc']).text = '1'
            etree.SubElement(
                payment, '{%s}PaymentMeansCode' % NS['cbc']
            ).text = data.payment_means_code
            etree.SubElement(
                payment, '{%s}PaymentDueDate' % NS['cbc']
            ).text = data.due_date or data.issue_date

            # Impuestos
            if impuestos_agrupados:
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
                f"Error construyendo documento soporte: {str(e)}"
            )

    def _add_ubl_extensions_support(
        self,
        doc: etree._Element,
        data: SupportDocumentData,
        cude: str,
        software_security_code: str
    ):
        """Agregar UBLExtensions para documento soporte."""
        extensions = etree.SubElement(doc, '{%s}UBLExtensions' % NS['ext'])

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
        id_country = etree.SubElement(
            inv_source, '{%s}IdentificationCode' % NS['cbc']
        )
        for attr, value in COUNTRY_ID_ATTRS.items():
            id_country.set(attr, value)
        id_country.text = 'CO'

        # SoftwareProvider
        software_prov = etree.SubElement(
            dian_ext, '{%s}SoftwareProvider' % NS['sts']
        )
        prov_id = etree.SubElement(
            software_prov, '{%s}ProviderID' % NS['sts']
        )
        prov_id.set('schemeAgencyID', '195')
        prov_id.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        prov_id.set('schemeID', str(calcular_dv(self.config.nit)))
        prov_id.set('schemeName', '31')
        prov_id.text = self.config.nit

        soft_id = etree.SubElement(
            software_prov, '{%s}SoftwareID' % NS['sts']
        )
        soft_id.set('schemeAgencyID', '195')
        soft_id.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        soft_id.text = self.config.software_id

        # SoftwareSecurityCode
        soft_sec = etree.SubElement(
            dian_ext, '{%s}SoftwareSecurityCode' % NS['sts']
        )
        soft_sec.set('schemeAgencyID', '195')
        soft_sec.set('schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName'])
        soft_sec.text = software_security_code

        # AuthorizationProvider
        auth_prov = etree.SubElement(
            dian_ext, '{%s}AuthorizationProvider' % NS['sts']
        )
        auth_prov_id = etree.SubElement(
            auth_prov, '{%s}AuthorizationProviderID' % NS['sts']
        )
        auth_prov_id.set('schemeAgencyID', '195')
        auth_prov_id.set(
            'schemeAgencyName', SCHEME_AGENCY_ATTRS['schemeAgencyName']
        )
        auth_prov_id.set('schemeID', '4')
        auth_prov_id.set('schemeName', '31')
        auth_prov_id.text = AUTHORIZATION_PROVIDER_ID

        # QRCode
        qr_base = (
            'https://catalogo-vpfe-hab.dian.gov.co'
            if self.config.environment == '2'
            else 'https://catalogo-vpfe.dian.gov.co'
        )
        qr_code = etree.SubElement(dian_ext, '{%s}QRCode' % NS['sts'])
        qr_code.text = f"{qr_base}/document/searchqr?documentkey={cude}"

        # Extension 2: Signature (vacio, se llena con firma)
        ext2 = etree.SubElement(extensions, '{%s}UBLExtension' % NS['ext'])
        etree.SubElement(ext2, '{%s}ExtensionContent' % NS['ext'])
