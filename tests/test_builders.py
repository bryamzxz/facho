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
from facho.fe.client.dian_simple import calcular_dv, calcular_cufe, calcular_cude


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
