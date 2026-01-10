#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Tests para los builders de documentos DIAN.
"""

import pytest
from datetime import datetime, timedelta
from lxml import etree

# Importar directamente de los modulos para evitar dependencias legacy
from facho.fe.builders.invoice_builder import (
    InvoiceBuilder,
    InvoiceConfig,
    InvoiceData,
    InvoiceLine,
    Party,
    Address,
)
from facho.fe.builders.credit_note_builder import CreditNoteBuilder, CreditNoteData
from facho.fe.builders.debit_note_builder import DebitNoteBuilder, DebitNoteData
from facho.fe.builders.constants import DOC_TYPES, CREDIT_REASONS, DEBIT_REASONS
from facho.fe.builders.taxes import (
    Tax,
    TaxTotal,
    truncar,
    formato_dinero,
    agrupar_impuestos,
    separar_impuestos_retenciones,
    calcular_totales_impuestos,
    TAX_CODES,
    TAX_NAMES,
    WITHHOLDING_TAX_CODES,
)
from facho.fe.client.dian_simple import (
    calcular_dv,
    calcular_cufe,
    calcular_cude,
    calcular_cufe_flexible,
    calcular_cude_flexible,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_config():
    """Configuracion de prueba."""
    return InvoiceConfig(
        software_id='1e3fa8f4-1a91-4028-9293-a9817406100f',
        software_pin='12345',
        technical_key='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
        test_set_id='e9015851-e8e1-4cee-99cc-470044cded3e',
        nit='1001186599',
        company_name='EMPRESA DE PRUEBA',
        resolution_number='18760000001',
        resolution_date='2019-01-19',
        resolution_end_date='2030-01-19',
        prefix='SETP',
        range_from='990000000',
        range_to='995000000',
        environment='2',
    )


@pytest.fixture
def sample_address():
    """Direccion de prueba."""
    return Address(
        city_code='68081',
        city_name='Bucaramanga',
        postal_zone='680001',
        country_subentity='Santander',
        country_subentity_code='68',
        address_line='Calle 123 # 45-67',
        country_code='CO',
        country_name='Colombia'
    )


@pytest.fixture
def sample_supplier(sample_address):
    """Proveedor de prueba."""
    return Party(
        nit='1001186599',
        name='EMPRESA DE PRUEBA',
        legal_name='EMPRESA DE PRUEBA S.A.S',
        organization_code='1',
        tax_level_code='R-99-PN',
        tax_scheme_code='01',
        tax_scheme_name='IVA',
        scheme_name='31',
        address=sample_address,
        email='empresa@test.com',
        responsability_regime_code='48',
    )


@pytest.fixture
def sample_customer(sample_address):
    """Cliente de prueba."""
    return Party(
        nit='222222222222',
        name='Consumidor Final',
        legal_name='Consumidor Final',
        organization_code='2',
        tax_level_code='R-99-PN',
        tax_scheme_code='01',
        tax_scheme_name='IVA',
        scheme_name='13',
        address=sample_address,
        email='cliente@test.com',
        responsability_regime_code='48',
    )


@pytest.fixture
def sample_lines():
    """Lineas de factura de prueba."""
    return [
        InvoiceLine(
            description='Producto de prueba 1',
            quantity=2.0,
            unit_code='94',
            unit_price=50000.0,
            tax_percent=19.0,
            item_id='PROD001',
        ),
        InvoiceLine(
            description='Servicio de prueba',
            quantity=1.0,
            unit_code='94',
            unit_price=100000.0,
            tax_percent=19.0,
            item_id='SERV001',
        ),
    ]


@pytest.fixture
def sample_invoice_data(sample_supplier, sample_customer, sample_lines):
    """Datos de factura de prueba."""
    return InvoiceData(
        number='SETP990000001',
        issue_date='2024-01-15',
        issue_time='10:30:00-05:00',
        due_date='2024-02-14',
        note='Factura de prueba',
        supplier=sample_supplier,
        customer=sample_customer,
        lines=sample_lines,
    )


# =============================================================================
# TESTS DE UTILIDADES
# =============================================================================

class TestCalcularDV:
    """Tests para calcular digito de verificacion."""

    def test_dv_conocido(self):
        """Test DV con NIT conocido."""
        assert calcular_dv('800197268') == 4  # DIAN

    def test_dv_otro_nit(self):
        """Test DV con otro NIT."""
        dv = calcular_dv('1001186599')
        assert isinstance(dv, int)
        assert 0 <= dv <= 9

    def test_dv_con_guiones(self):
        """Test DV ignorando caracteres no numericos."""
        assert calcular_dv('800-197-268') == calcular_dv('800197268')


class TestCalcularCUFE:
    """Tests para calcular CUFE."""

    def test_cufe_formato(self):
        """Test que CUFE tenga formato correcto (SHA-384 hex)."""
        cufe = calcular_cufe(
            numero='SETP990000001',
            fecha_emision='2024-01-15',
            hora_emision='10:30:00-05:00',
            subtotal=100000.0,
            iva=19000.0,
            total=119000.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            clave_tecnica='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            tipo_ambiente='2'
        )
        # SHA-384 produce 96 caracteres hexadecimales
        assert len(cufe) == 96
        assert all(c in '0123456789abcdef' for c in cufe)

    def test_cufe_deterministico(self):
        """Test que CUFE sea deterministico."""
        params = dict(
            numero='SETP990000001',
            fecha_emision='2024-01-15',
            hora_emision='10:30:00-05:00',
            subtotal=100000.0,
            iva=19000.0,
            total=119000.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            clave_tecnica='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            tipo_ambiente='2'
        )
        cufe1 = calcular_cufe(**params)
        cufe2 = calcular_cufe(**params)
        assert cufe1 == cufe2

    def test_cufe_diferente_con_diferentes_datos(self):
        """Test que diferentes datos produzcan diferentes CUFEs."""
        base_params = dict(
            numero='SETP990000001',
            fecha_emision='2024-01-15',
            hora_emision='10:30:00-05:00',
            subtotal=100000.0,
            iva=19000.0,
            total=119000.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            clave_tecnica='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            tipo_ambiente='2'
        )

        cufe1 = calcular_cufe(**base_params)

        # Cambiar numero de factura
        params2 = {**base_params, 'numero': 'SETP990000002'}
        cufe2 = calcular_cufe(**params2)

        assert cufe1 != cufe2


class TestCalcularCUDE:
    """Tests para calcular CUDE."""

    def test_cude_formato(self):
        """Test que CUDE tenga formato correcto (SHA-384 hex)."""
        cude = calcular_cude(
            numero='SETP990000001',
            fecha_emision='2024-01-15',
            hora_emision='10:30:00-05:00',
            subtotal=100000.0,
            iva=19000.0,
            total=119000.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            software_pin='12345',
            tipo_ambiente='2'
        )
        assert len(cude) == 96
        assert all(c in '0123456789abcdef' for c in cude)

    def test_cude_diferente_de_cufe(self):
        """Test que CUDE sea diferente de CUFE (usa PIN, no clave tecnica)."""
        cufe = calcular_cufe(
            numero='SETP990000001',
            fecha_emision='2024-01-15',
            hora_emision='10:30:00-05:00',
            subtotal=100000.0,
            iva=19000.0,
            total=119000.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            clave_tecnica='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            tipo_ambiente='2'
        )

        cude = calcular_cude(
            numero='SETP990000001',
            fecha_emision='2024-01-15',
            hora_emision='10:30:00-05:00',
            subtotal=100000.0,
            iva=19000.0,
            total=119000.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            software_pin='12345',
            tipo_ambiente='2'
        )

        assert cufe != cude


# =============================================================================
# TESTS DE INVOICE BUILDER
# =============================================================================

class TestInvoiceBuilder:
    """Tests para InvoiceBuilder."""

    def test_build_invoice_xml(self, sample_config, sample_invoice_data):
        """Test construccion de factura XML."""
        builder = InvoiceBuilder(sample_config)
        xml = builder.build(sample_invoice_data)

        assert xml is not None
        assert xml.tag == 'Invoice'

    def test_invoice_has_cufe(self, sample_config, sample_invoice_data):
        """Test que factura tenga CUFE."""
        builder = InvoiceBuilder(sample_config)
        xml = builder.build(sample_invoice_data)

        uuid_el = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID')
        assert uuid_el is not None
        assert len(uuid_el.text) == 96  # SHA-384

    def test_invoice_has_dian_extensions(self, sample_config, sample_invoice_data):
        """Test que factura tenga extensiones DIAN."""
        builder = InvoiceBuilder(sample_config)
        xml = builder.build(sample_invoice_data)

        dian_ext = xml.find('.//{dian:gov:co:facturaelectronica:Structures-2-1}DianExtensions')
        assert dian_ext is not None

    def test_invoice_has_supplier(self, sample_config, sample_invoice_data):
        """Test que factura tenga proveedor."""
        builder = InvoiceBuilder(sample_config)
        xml = builder.build(sample_invoice_data)

        supplier = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty')
        assert supplier is not None

    def test_invoice_has_customer(self, sample_config, sample_invoice_data):
        """Test que factura tenga cliente."""
        builder = InvoiceBuilder(sample_config)
        xml = builder.build(sample_invoice_data)

        customer = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty')
        assert customer is not None


# =============================================================================
# TESTS DE CREDIT NOTE BUILDER
# =============================================================================

class TestCreditNoteBuilder:
    """Tests para CreditNoteBuilder."""

    def test_build_credit_note_xml(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test construccion de nota credito XML."""
        credit_note_data = CreditNoteData(
            number='SETP990000002',
            issue_date='2024-01-16',
            issue_time='11:00:00-05:00',
            note='Nota credito de prueba',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
            discrepancy_response_code='2',
            discrepancy_description='Anulacion',
        )

        builder = CreditNoteBuilder(sample_config)
        xml = builder.build(credit_note_data)

        assert xml is not None
        assert xml.tag == 'CreditNote'

    def test_credit_note_has_cude(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test que nota credito tenga CUDE."""
        credit_note_data = CreditNoteData(
            number='SETP990000002',
            issue_date='2024-01-16',
            issue_time='11:00:00-05:00',
            note='Nota credito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
        )

        builder = CreditNoteBuilder(sample_config)
        xml = builder.build(credit_note_data)

        uuid_el = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID')
        assert uuid_el is not None
        assert uuid_el.get('schemeName') == 'CUDE-SHA384'

    def test_credit_note_has_billing_reference(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test que nota credito tenga referencia a factura."""
        credit_note_data = CreditNoteData(
            number='SETP990000002',
            issue_date='2024-01-16',
            issue_time='11:00:00-05:00',
            note='Nota credito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
        )

        builder = CreditNoteBuilder(sample_config)
        xml = builder.build(credit_note_data)

        billing_ref = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}BillingReference')
        assert billing_ref is not None


# =============================================================================
# TESTS DE DEBIT NOTE BUILDER
# =============================================================================

class TestDebitNoteBuilder:
    """Tests para DebitNoteBuilder."""

    def test_build_debit_note_xml(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test construccion de nota debito XML."""
        debit_note_data = DebitNoteData(
            number='SETP990000003',
            issue_date='2024-01-17',
            issue_time='09:00:00-05:00',
            note='Nota debito de prueba',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
            discrepancy_response_code='1',
            discrepancy_description='Intereses',
        )

        builder = DebitNoteBuilder(sample_config)
        xml = builder.build(debit_note_data)

        assert xml is not None
        assert xml.tag == 'DebitNote'

    def test_debit_note_has_cude(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test que nota debito tenga CUDE."""
        debit_note_data = DebitNoteData(
            number='SETP990000003',
            issue_date='2024-01-17',
            issue_time='09:00:00-05:00',
            note='Nota debito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
        )

        builder = DebitNoteBuilder(sample_config)
        xml = builder.build(debit_note_data)

        uuid_el = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID')
        assert uuid_el is not None
        assert uuid_el.get('schemeName') == 'CUDE-SHA384'

    def test_debit_note_has_discrepancy_response(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test que nota debito tenga respuesta de discrepancia."""
        debit_note_data = DebitNoteData(
            number='SETP990000003',
            issue_date='2024-01-17',
            issue_time='09:00:00-05:00',
            note='Nota debito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
            discrepancy_response_code='1',
        )

        builder = DebitNoteBuilder(sample_config)
        xml = builder.build(debit_note_data)

        disc_resp = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}DiscrepancyResponse')
        assert disc_resp is not None

    def test_debit_note_has_requested_monetary_total(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test que nota debito tenga RequestedMonetaryTotal (no LegalMonetaryTotal)."""
        debit_note_data = DebitNoteData(
            number='SETP990000003',
            issue_date='2024-01-17',
            issue_time='09:00:00-05:00',
            note='Nota debito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
        )

        builder = DebitNoteBuilder(sample_config)
        xml = builder.build(debit_note_data)

        req_monetary = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}RequestedMonetaryTotal')
        assert req_monetary is not None

    def test_debit_note_lines(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test que nota debito tenga lineas DebitNoteLine."""
        debit_note_data = DebitNoteData(
            number='SETP990000003',
            issue_date='2024-01-17',
            issue_time='09:00:00-05:00',
            note='Nota debito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
        )

        builder = DebitNoteBuilder(sample_config)
        xml = builder.build(debit_note_data)

        debit_lines = xml.findall('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}DebitNoteLine')
        assert len(debit_lines) == len(sample_lines)


# =============================================================================
# TESTS DE CONSTANTES
# =============================================================================

class TestConstants:
    """Tests para constantes."""

    def test_doc_types_has_all_types(self):
        """Test que DOC_TYPES tenga todos los tipos."""
        assert 'factura' in DOC_TYPES
        assert 'credito' in DOC_TYPES
        assert 'debito' in DOC_TYPES

    def test_doc_types_codes(self):
        """Test codigos de tipo de documento."""
        assert DOC_TYPES['factura']['code'] == '01'
        assert DOC_TYPES['credito']['code'] == '91'
        assert DOC_TYPES['debito']['code'] == '92'

    def test_credit_reasons(self):
        """Test motivos de notas credito."""
        assert '1' in CREDIT_REASONS
        assert '2' in CREDIT_REASONS
        assert '3' in CREDIT_REASONS
        assert '4' in CREDIT_REASONS

    def test_debit_reasons(self):
        """Test motivos de notas debito."""
        assert '1' in DEBIT_REASONS
        assert '2' in DEBIT_REASONS
        assert '3' in DEBIT_REASONS
        assert '4' in DEBIT_REASONS

    def test_customization_ids(self):
        """Test CustomizationID por tipo de documento."""
        assert DOC_TYPES['factura']['customization_id'] == '10'
        assert DOC_TYPES['credito']['customization_id'] == '20'
        assert DOC_TYPES['debito']['customization_id'] == '30'

    def test_uuid_names(self):
        """Test nombres de UUID por tipo de documento."""
        assert DOC_TYPES['factura']['uuid_name'] == 'CUFE-SHA384'
        assert DOC_TYPES['credito']['uuid_name'] == 'CUDE-SHA384'
        assert DOC_TYPES['debito']['uuid_name'] == 'CUDE-SHA384'


# =============================================================================
# TESTS DE CUSTOMIZATION ID EN XML
# =============================================================================

class TestCustomizationIDInXML:
    """Tests para verificar CustomizationID correcto en XML generado."""

    def test_invoice_customization_id(self, sample_config, sample_invoice_data):
        """Test que factura tenga CustomizationID=10."""
        builder = InvoiceBuilder(sample_config)
        xml = builder.build(sample_invoice_data)

        cust_id = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID')
        assert cust_id is not None
        assert cust_id.text == '10'

    def test_credit_note_customization_id(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test que nota credito tenga CustomizationID=20."""
        credit_note_data = CreditNoteData(
            number='SETP990000002',
            issue_date='2024-01-16',
            issue_time='11:00:00-05:00',
            note='Nota credito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
        )

        builder = CreditNoteBuilder(sample_config)
        xml = builder.build(credit_note_data)

        cust_id = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID')
        assert cust_id is not None
        assert cust_id.text == '20'

    def test_debit_note_customization_id(self, sample_config, sample_supplier, sample_customer, sample_lines):
        """Test que nota debito tenga CustomizationID=30."""
        debit_note_data = DebitNoteData(
            number='SETP990000003',
            issue_date='2024-01-17',
            issue_time='09:00:00-05:00',
            note='Nota debito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
        )

        builder = DebitNoteBuilder(sample_config)
        xml = builder.build(debit_note_data)

        cust_id = xml.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID')
        assert cust_id is not None
        assert cust_id.text == '30'


# =============================================================================
# TESTS DE ORDEN DE ELEMENTOS EN NOTAS
# =============================================================================

class TestElementOrder:
    """Tests para verificar orden correcto de elementos en notas."""

    def test_discrepancy_before_billing_reference_credit_note(
        self, sample_config, sample_supplier, sample_customer, sample_lines
    ):
        """Test que DiscrepancyResponse venga ANTES de BillingReference en nota credito."""
        credit_note_data = CreditNoteData(
            number='SETP990000002',
            issue_date='2024-01-16',
            issue_time='11:00:00-05:00',
            note='Nota credito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
        )

        builder = CreditNoteBuilder(sample_config)
        xml = builder.build(credit_note_data)

        # Obtener indices de los elementos
        children = list(xml)
        discrepancy_idx = None
        billing_idx = None

        for idx, child in enumerate(children):
            if 'DiscrepancyResponse' in child.tag:
                discrepancy_idx = idx
            if 'BillingReference' in child.tag:
                billing_idx = idx

        assert discrepancy_idx is not None, "DiscrepancyResponse no encontrado"
        assert billing_idx is not None, "BillingReference no encontrado"
        assert discrepancy_idx < billing_idx, \
            f"DiscrepancyResponse (idx={discrepancy_idx}) debe estar ANTES de BillingReference (idx={billing_idx})"

    def test_discrepancy_before_billing_reference_debit_note(
        self, sample_config, sample_supplier, sample_customer, sample_lines
    ):
        """Test que DiscrepancyResponse venga ANTES de BillingReference en nota debito."""
        debit_note_data = DebitNoteData(
            number='SETP990000003',
            issue_date='2024-01-17',
            issue_time='09:00:00-05:00',
            note='Nota debito',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=sample_lines,
            billing_reference_id='SETP990000001',
            billing_reference_uuid='a' * 96,
            billing_reference_date='2024-01-15',
        )

        builder = DebitNoteBuilder(sample_config)
        xml = builder.build(debit_note_data)

        # Obtener indices de los elementos
        children = list(xml)
        discrepancy_idx = None
        billing_idx = None

        for idx, child in enumerate(children):
            if 'DiscrepancyResponse' in child.tag:
                discrepancy_idx = idx
            if 'BillingReference' in child.tag:
                billing_idx = idx

        assert discrepancy_idx is not None, "DiscrepancyResponse no encontrado"
        assert billing_idx is not None, "BillingReference no encontrado"
        assert discrepancy_idx < billing_idx, \
            f"DiscrepancyResponse (idx={discrepancy_idx}) debe estar ANTES de BillingReference (idx={billing_idx})"


# =============================================================================
# TESTS DE SISTEMA DE IMPUESTOS FLEXIBLE (FASE 1)
# =============================================================================

class TestTruncamiento:
    """Tests para funciones de truncamiento."""

    def test_truncar_no_redondea(self):
        """Test que truncar no redondee."""
        assert truncar(123.456789, 2) == 123.45
        assert truncar(99.999, 2) == 99.99
        assert truncar(1.005, 2) == 1.00  # No redondea a 1.01

    def test_truncar_diferentes_decimales(self):
        """Test truncar con diferentes decimales."""
        assert truncar(123.456789, 0) == 123.0
        assert truncar(123.456789, 1) == 123.4
        assert truncar(123.456789, 4) == 123.4567

    def test_formato_dinero(self):
        """Test formato monetario."""
        assert formato_dinero(123.456) == '123.45'
        assert formato_dinero(100000) == '100000.00'
        assert formato_dinero(0.999) == '0.99'


class TestTaxDataclass:
    """Tests para la clase Tax."""

    def test_tax_iva_19(self):
        """Test creacion de IVA 19%."""
        tax = Tax.iva_19(100000.0)
        assert tax.code == '01'
        assert tax.name == 'IVA'
        assert tax.percent == 19.0
        assert tax.taxable_amount == 100000.0
        assert tax.amount == 19000.0
        assert tax.is_withholding is False

    def test_tax_iva_5(self):
        """Test creacion de IVA 5%."""
        tax = Tax.iva_5(100000.0)
        assert tax.code == '01'
        assert tax.percent == 5.0
        assert tax.amount == 5000.0

    def test_tax_iva_0(self):
        """Test creacion de IVA 0%."""
        tax = Tax.iva_0(100000.0)
        assert tax.code == '01'
        assert tax.percent == 0.0
        assert tax.amount == 0.0

    def test_tax_ica(self):
        """Test creacion de ICA."""
        tax = Tax.ica(0.966, 100000.0)
        assert tax.code == '03'
        assert tax.name == 'ICA'
        assert tax.percent == 0.966
        assert tax.amount == 966.0
        assert tax.is_withholding is False

    def test_tax_inc(self):
        """Test creacion de INC."""
        tax = Tax.inc(8.0, 100000.0)
        assert tax.code == '04'
        assert tax.name == 'INC'
        assert tax.percent == 8.0
        assert tax.amount == 8000.0

    def test_tax_rete_fte(self):
        """Test creacion de retencion en la fuente."""
        tax = Tax.rete_fte(11.0, 100000.0)
        assert tax.code == '06'
        assert tax.name == 'ReteFte'
        assert tax.percent == 11.0
        assert tax.amount == 11000.0
        assert tax.is_withholding is True

    def test_tax_rete_iva(self):
        """Test creacion de retencion de IVA."""
        iva_amount = 19000.0
        tax = Tax.rete_iva(iva_amount, 15.0)
        assert tax.code == '05'
        assert tax.name == 'ReteIVA'
        assert tax.percent == 15.0
        assert tax.amount == 2850.0  # 15% de 19000
        assert tax.is_withholding is True

    def test_tax_rete_ica(self):
        """Test creacion de retencion de ICA."""
        tax = Tax.rete_ica(1.2, 100000.0)
        assert tax.code == '07'
        assert tax.name == 'ReteICA'
        assert tax.is_withholding is True

    def test_withholding_codes(self):
        """Test que codigos de retencion se detecten correctamente."""
        assert '05' in WITHHOLDING_TAX_CODES  # ReteIVA
        assert '06' in WITHHOLDING_TAX_CODES  # ReteFte
        assert '07' in WITHHOLDING_TAX_CODES  # ReteICA
        assert '01' not in WITHHOLDING_TAX_CODES  # IVA no es retencion


class TestAgruparImpuestos:
    """Tests para agrupacion de impuestos."""

    def test_agrupar_impuestos_mismo_codigo(self):
        """Test agrupacion de impuestos del mismo codigo."""
        taxes = [
            Tax.iva_19(50000.0),  # 9500
            Tax.iva_19(30000.0),  # 5700
        ]
        agrupados = agrupar_impuestos(taxes)

        assert '01' in agrupados
        assert agrupados['01'].total_amount == 15200.0
        assert agrupados['01'].total_taxable_amount == 80000.0

    def test_agrupar_impuestos_diferentes_codigos(self):
        """Test agrupacion de impuestos de diferentes codigos."""
        taxes = [
            Tax.iva_19(100000.0),
            Tax.ica(0.966, 100000.0),
        ]
        agrupados = agrupar_impuestos(taxes)

        assert '01' in agrupados
        assert '03' in agrupados
        assert agrupados['01'].total_amount == 19000.0
        assert agrupados['03'].total_amount == 966.0

    def test_separar_impuestos_retenciones(self):
        """Test separacion de impuestos regulares y retenciones."""
        taxes = [
            Tax.iva_19(100000.0),
            Tax.rete_fte(11.0, 100000.0),
            Tax.rete_iva(19000.0),
        ]
        impuestos, retenciones = separar_impuestos_retenciones(taxes)

        assert len(impuestos) == 1
        assert len(retenciones) == 2
        assert impuestos[0].code == '01'
        assert all(t.is_withholding for t in retenciones)


class TestCalcularTotalesImpuestos:
    """Tests para calculo de totales de impuestos."""

    def test_calcular_totales_impuestos(self):
        """Test calculo de totales por codigo."""
        taxes = [
            Tax.iva_19(100000.0),
            Tax.iva_5(50000.0),
            Tax.ica(0.966, 100000.0),
        ]
        totales = calcular_totales_impuestos(taxes)

        assert totales['01'] == 21500.0  # 19000 + 2500
        assert totales['03'] == 966.0


class TestCUFEFlexible:
    """Tests para calculo de CUFE/CUDE con multiples impuestos."""

    def test_cufe_flexible_formato(self):
        """Test que CUFE flexible tenga formato correcto."""
        cufe = calcular_cufe_flexible(
            numero='SETP990000001',
            fecha_emision='2024-01-15',
            hora_emision='10:30:00-05:00',
            subtotal=100000.0,
            impuestos={'01': 19000.0, '03': 966.0, '04': 0.0},
            total=119966.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            clave_tecnica='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            tipo_ambiente='2'
        )
        assert len(cufe) == 96
        assert all(c in '0123456789abcdef' for c in cufe)

    def test_cufe_flexible_compatible_con_legacy(self):
        """Test que CUFE flexible sea compatible con legacy cuando solo hay IVA."""
        cufe_legacy = calcular_cufe(
            numero='SETP990000001',
            fecha_emision='2024-01-15',
            hora_emision='10:30:00-05:00',
            subtotal=100000.0,
            iva=19000.0,
            total=119000.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            clave_tecnica='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            tipo_ambiente='2'
        )

        cufe_flexible = calcular_cufe_flexible(
            numero='SETP990000001',
            fecha_emision='2024-01-15',
            hora_emision='10:30:00-05:00',
            subtotal=100000.0,
            impuestos={'01': 19000.0},
            total=119000.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            clave_tecnica='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            tipo_ambiente='2'
        )

        assert cufe_legacy == cufe_flexible

    def test_cude_flexible_formato(self):
        """Test que CUDE flexible tenga formato correcto."""
        cude = calcular_cude_flexible(
            numero='SETP990000002',
            fecha_emision='2024-01-16',
            hora_emision='11:00:00-05:00',
            subtotal=100000.0,
            impuestos={'01': 19000.0, '03': 500.0},
            total=119500.0,
            nit_emisor='1001186599',
            nit_adquiriente='222222222222',
            software_pin='12345',
            tipo_ambiente='2'
        )
        assert len(cude) == 96


class TestInvoiceLineMultipleTaxes:
    """Tests para lineas de factura con multiples impuestos."""

    def test_invoice_line_legacy_mode(self):
        """Test que modo legacy funcione (solo tax_percent)."""
        line = InvoiceLine(
            description='Producto',
            quantity=2.0,
            unit_code='94',
            unit_price=50000.0,
            tax_percent=19.0,
        )

        assert len(line.taxes) == 1
        assert line.taxes[0].code == '01'
        assert line.taxes[0].percent == 19.0
        assert line.get_line_total() == 100000.0
        assert line.get_taxes_total() == 19000.0

    def test_invoice_line_multiple_taxes(self):
        """Test linea con multiples impuestos."""
        line_total = 100000.0
        line = InvoiceLine(
            description='Producto',
            quantity=1.0,
            unit_code='94',
            unit_price=100000.0,
            taxes=[
                Tax.iva_19(line_total),
                Tax.ica(0.966, line_total),
            ]
        )

        assert len(line.taxes) == 2
        assert line.get_line_total() == 100000.0
        assert line.get_taxes_total() == 19966.0  # 19000 + 966

    def test_invoice_line_with_withholdings(self):
        """Test linea con retenciones."""
        line_total = 100000.0
        line = InvoiceLine(
            description='Servicio',
            quantity=1.0,
            unit_code='94',
            unit_price=100000.0,
            taxes=[
                Tax.iva_19(line_total),
                Tax.rete_fte(11.0, line_total),
            ]
        )

        assert line.get_taxes_total() == 19000.0  # Solo IVA
        assert line.get_withholdings_total() == 11000.0  # ReteFte

    def test_invoice_line_get_iva(self):
        """Test obtener IVA de la linea."""
        line = InvoiceLine(
            description='Producto',
            quantity=1.0,
            unit_code='94',
            unit_price=100000.0,
            taxes=[
                Tax.iva_19(100000.0),
                Tax.ica(0.5, 100000.0),
            ]
        )

        iva = line.get_iva()
        assert iva is not None
        assert iva.code == '01'
        assert iva.amount == 19000.0


class TestInvoiceBuilderMultipleTaxes:
    """Tests para InvoiceBuilder con multiples impuestos."""

    def test_invoice_with_multiple_tax_rates(self, sample_config, sample_supplier, sample_customer):
        """Test factura con IVA 19% y 5%."""
        lines = [
            InvoiceLine(
                description='Producto IVA 19%',
                quantity=1.0,
                unit_code='94',
                unit_price=100000.0,
                taxes=[Tax.iva_19(100000.0)]
            ),
            InvoiceLine(
                description='Producto IVA 5%',
                quantity=1.0,
                unit_code='94',
                unit_price=50000.0,
                taxes=[Tax.iva_5(50000.0)]
            ),
        ]

        invoice_data = InvoiceData(
            number='SETP990000010',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
            due_date='2024-02-14',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=lines,
        )

        builder = InvoiceBuilder(sample_config)
        xml = builder.build(invoice_data)

        # Debe tener TaxTotal
        tax_totals = xml.findall('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal')
        assert len(tax_totals) >= 1

    def test_invoice_with_iva_and_ica(self, sample_config, sample_supplier, sample_customer):
        """Test factura con IVA e ICA."""
        line_total = 100000.0
        lines = [
            InvoiceLine(
                description='Producto con IVA e ICA',
                quantity=1.0,
                unit_code='94',
                unit_price=100000.0,
                taxes=[
                    Tax.iva_19(line_total),
                    Tax.ica(0.966, line_total),
                ]
            ),
        ]

        invoice_data = InvoiceData(
            number='SETP990000011',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=lines,
        )

        builder = InvoiceBuilder(sample_config)
        xml = builder.build(invoice_data)

        # Contar TaxTotal a nivel de documento (hijos directos)
        # Hay 2 a nivel documento (IVA e ICA) + 2 a nivel de linea
        cac_ns = '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}'
        doc_tax_totals = [child for child in xml if child.tag == f'{cac_ns}TaxTotal']
        assert len(doc_tax_totals) == 2  # Uno para IVA, otro para ICA

    def test_invoice_with_withholdings(self, sample_config, sample_supplier, sample_customer):
        """Test factura con retenciones."""
        line_total = 100000.0
        iva_amount = 19000.0
        lines = [
            InvoiceLine(
                description='Servicio con retenciones',
                quantity=1.0,
                unit_code='94',
                unit_price=100000.0,
                taxes=[
                    Tax.iva_19(line_total),
                    Tax.rete_fte(11.0, line_total),
                    Tax.rete_iva(iva_amount, 15.0),
                ]
            ),
        ]

        invoice_data = InvoiceData(
            number='SETP990000012',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
            supplier=sample_supplier,
            customer=sample_customer,
            lines=lines,
        )

        builder = InvoiceBuilder(sample_config)
        xml = builder.build(invoice_data)

        # Debe tener WithholdingTaxTotal
        wh_totals = xml.findall('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}WithholdingTaxTotal')
        assert len(wh_totals) == 2  # ReteFte y ReteIVA
