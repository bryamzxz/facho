# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Constructor de Documento Equivalente POS (tipo 03) para DIAN Colombia.

Caracteristicas:
- Para ventas menores a 5 UVT
- Cliente puede ser consumidor final generico (222222222222)
- Usa CUDE (no CUFE)
- Requiere numero de caja/terminal
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional
from lxml import etree

from .constants import (
    NS,
    SCHEME_AGENCY_ATTRS,
    DIAN_UBL_VERSION,
    COUNTRY_ID_ATTRS,
    AUTHORIZATION_PROVIDER_ID,
    GENERIC_CONSUMER,
    UVT_VALUES,
)
from .taxes import (
    Tax,
    agrupar_impuestos,
    separar_impuestos_retenciones,
    calcular_totales_impuestos,
    truncar,
    formato_dinero,
)
from .cufe import CufeInput, calculate_cude, calculate_software_security_code
from .invoice_builder import InvoiceBuilder, InvoiceConfig, InvoiceLine, Party, Address
from .exceptions import ValidationError, XmlBuildError, UvtLimitExceededError
from .validators import validate_before_build, validate_pos_limits
from ..client.dian_simple import calcular_dv


POS_DOCUMENT_TYPE_CODE = '03'
POS_DOCUMENT_PROFILE_ID = 'DIAN 2.1: Factura Electronica de Venta'
POS_UVT_LIMIT = 5  # Limite de 5 UVT para documento POS


@dataclass
class PosDocumentData:
    """
    Datos del documento equivalente POS.

    Attributes:
        number: Numero del documento
        issue_date: Fecha de emision (YYYY-MM-DD)
        issue_time: Hora de emision (HH:MM:SS-05:00)
        due_date: Fecha de vencimiento (opcional)
        note: Nota del documento
        supplier: Datos del vendedor
        customer: Datos del comprador (puede ser consumidor generico)
        lines: Lineas del documento
        terminal_id: ID de la caja/terminal POS
        sequence_prefix: Prefijo de consecutivo (opcional)
        payment_means_code: Codigo de medio de pago (default '10' = efectivo)
    """
    number: str
    issue_date: str
    issue_time: str
    due_date: str = None
    note: str = 'Documento equivalente POS'
    supplier: Party = None
    customer: Party = None
    lines: List[InvoiceLine] = field(default_factory=list)
    terminal_id: str = ''
    sequence_prefix: str = 'POS'
    payment_means_code: str = '10'

    def use_generic_consumer(self):
        """Establecer cliente como consumidor final generico."""
        self.customer = Party(
            nit=GENERIC_CONSUMER['nit'],
            name=GENERIC_CONSUMER['name'],
            legal_name=GENERIC_CONSUMER['name'],
            scheme_name=GENERIC_CONSUMER['doc_type'],
            organization_code='2',  # Persona natural
        )

    @staticmethod
    def get_uvt_value(year: int = None) -> float:
        """
        Obtener valor UVT del ano.

        Args:
            year: Ano (default: ano actual)

        Returns:
            Valor del UVT
        """
        if year is None:
            year = datetime.now().year
        return UVT_VALUES.get(year, UVT_VALUES[max(UVT_VALUES.keys())])

    def get_max_value(self, year: int = None) -> float:
        """
        Obtener valor maximo para documento POS.

        Args:
            year: Ano (default: ano actual)

        Returns:
            Valor maximo permitido
        """
        return POS_UVT_LIMIT * self.get_uvt_value(year)


class PosDocumentBuilder(InvoiceBuilder):
    """
    Constructor de Documento Equivalente POS para DIAN.

    El documento POS se utiliza para ventas de bajo monto
    (menores a 5 UVT).

    Example:
        config = InvoiceConfig(...)

        data = PosDocumentData(
            number='POS0001',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
            supplier=supplier,
            terminal_id='CAJA001',
            lines=[InvoiceLine(...)]
        )
        # Usar consumidor generico si no se tiene cliente
        data.use_generic_consumer()

        builder = PosDocumentBuilder(config)
        xml = builder.build(data)
    """

    def __init__(self, config: InvoiceConfig, uvt_year: int = None):
        """
        Inicializar builder POS.

        Args:
            config: Configuracion de facturacion
            uvt_year: Ano para calcular valor UVT (default: ano actual)
        """
        super().__init__(config)
        self.uvt_year = uvt_year or datetime.now().year
        self.uvt_value = UVT_VALUES.get(
            self.uvt_year,
            UVT_VALUES[max(UVT_VALUES.keys())]
        )
        self.uvt_limit = POS_UVT_LIMIT
        self.max_value = self.uvt_limit * self.uvt_value

    def build(self, data: PosDocumentData, validate_uvt: bool = True) -> etree._Element:
        """
        Construir XML de documento POS.

        Args:
            data: Datos del documento POS
            validate_uvt: Si se debe validar el limite UVT

        Returns:
            Elemento XML del documento

        Raises:
            UvtLimitExceededError: Si el total excede el limite de 5 UVT
        """
        try:
            # Si no hay cliente, usar generico
            if data.customer is None:
                data.use_generic_consumer()

            # Validar datos
            validate_before_build(data, self.config, "documento POS")

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

            # Total documento
            total = truncar(subtotal + total_impuestos)

            # Validar limite UVT
            if validate_uvt:
                errors = validate_pos_limits(total, self.uvt_limit, self.uvt_value)
                if errors:
                    raise UvtLimitExceededError(
                        total=total,
                        uvt_limit=self.uvt_limit,
                        uvt_value=self.uvt_value
                    )

            # Calcular CUDE (documento POS usa CUDE con SoftwarePIN)
            cufe_input = CufeInput(
                number=data.number,
                issue_date=data.issue_date,
                issue_time=data.issue_time,
                subtotal=subtotal,
                iva_amount=totales_impuestos.get('01', 0.0),
                inc_amount=totales_impuestos.get('04', 0.0),
                ica_amount=totales_impuestos.get('03', 0.0),
                total=total,
                supplier_nit=self.config.nit,
                customer_nit=data.customer.nit,
                technical_key=self.config.software_pin,  # PIN para CUDE
                environment=self.config.environment,
            )
            cude = calculate_cude(cufe_input)

            software_security_code = calculate_software_security_code(
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
            self._add_ubl_extensions_pos(
                doc, data, cude, software_security_code
            )

            # Campos principales
            etree.SubElement(
                doc, '{%s}UBLVersionID' % NS['cbc']
            ).text = DIAN_UBL_VERSION
            etree.SubElement(
                doc, '{%s}CustomizationID' % NS['cbc']
            ).text = '10'
            etree.SubElement(
                doc, '{%s}ProfileID' % NS['cbc']
            ).text = POS_DOCUMENT_PROFILE_ID
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
            inv_type.text = POS_DOCUMENT_TYPE_CODE

            # Nota
            if data.note:
                etree.SubElement(doc, '{%s}Note' % NS['cbc']).text = data.note

            # Terminal ID en nota adicional
            if data.terminal_id:
                etree.SubElement(
                    doc, '{%s}Note' % NS['cbc']
                ).text = f"Terminal: {data.terminal_id}"

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

            # Totales monetarios
            self._add_monetary_total(doc, subtotal, total_impuestos, total)

            # Lineas
            self._add_invoice_lines(doc, data.lines)

            return doc

        except (ValidationError, UvtLimitExceededError):
            raise
        except Exception as e:
            raise XmlBuildError(
                f"Error construyendo documento POS: {str(e)}"
            )

    def _add_ubl_extensions_pos(
        self,
        doc: etree._Element,
        data: PosDocumentData,
        cude: str,
        software_security_code: str
    ):
        """Agregar UBLExtensions para documento POS."""
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
