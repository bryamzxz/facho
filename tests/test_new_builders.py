# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Tests para los nuevos builders y funcionalidades de Facho.
"""

import pytest
from datetime import datetime


class TestExceptions:
    """Tests para el sistema de excepciones."""

    def test_facho_error_basic(self):
        from facho.fe.builders.exceptions import FachoError

        error = FachoError("Test error", code="TEST_001")
        assert str(error) == "[TEST_001] Test error"
        assert error.code == "TEST_001"
        assert error.message == "Test error"

    def test_facho_error_to_dict(self):
        from facho.fe.builders.exceptions import FachoError

        error = FachoError("Test error", code="TEST", details={'key': 'value'})
        result = error.to_dict()
        assert result['type'] == 'FachoError'
        assert result['code'] == 'TEST'
        assert result['details']['key'] == 'value'

    def test_validation_error(self):
        from facho.fe.builders.exceptions import ValidationError

        error = ValidationError(
            "Invalid data",
            errors=["Error 1", "Error 2"],
            field="test_field"
        )
        assert "Error 1" in str(error)
        assert "Error 2" in str(error)
        assert error.field == "test_field"

    def test_dian_error(self):
        from facho.fe.builders.exceptions import DianError

        error = DianError(
            "DIAN rejected",
            status_code="500",
            dian_errors=["FAB01: XML mal formado"],
            track_id="12345"
        )
        assert "FAB01" in str(error)
        assert error.track_id == "12345"

    def test_dian_error_codes(self):
        from facho.fe.builders.exceptions import (
            DIAN_ERROR_CODES,
            get_dian_error_description
        )

        assert 'FAB01' in DIAN_ERROR_CODES
        assert get_dian_error_description('FAB01') == 'XML mal formado'
        assert 'Error DIAN' in get_dian_error_description('UNKNOWN')

    def test_parse_dian_errors(self):
        from facho.fe.builders.exceptions import parse_dian_errors

        errors = parse_dian_errors(["FAB01: XML mal formado", "Unknown error"])
        assert len(errors) == 2
        assert errors[0]['code'] == 'FAB01'
        assert errors[0]['known_error'] is True
        assert errors[1]['code'] is None


class TestValidators:
    """Tests para los validadores."""

    def test_validate_nit_valid(self):
        from facho.fe.builders.validators import validate_nit

        errors = validate_nit("900123456")
        assert len(errors) == 0

        errors = validate_nit("9001234567")
        assert len(errors) == 0

    def test_validate_nit_invalid(self):
        from facho.fe.builders.validators import validate_nit

        errors = validate_nit("123")
        assert len(errors) > 0

        errors = validate_nit("")
        assert len(errors) > 0

    def test_validate_date_valid(self):
        from facho.fe.builders.validators import validate_date

        errors = validate_date("2024-01-15")
        assert len(errors) == 0

    def test_validate_date_invalid(self):
        from facho.fe.builders.validators import validate_date

        errors = validate_date("01-15-2024")
        assert len(errors) > 0

        errors = validate_date("2024-13-01")
        assert len(errors) > 0

    def test_validate_time_valid(self):
        from facho.fe.builders.validators import validate_time

        errors = validate_time("10:30:00-05:00")
        assert len(errors) == 0

    def test_validate_time_invalid(self):
        from facho.fe.builders.validators import validate_time

        errors = validate_time("10:30:00")
        assert len(errors) > 0

    def test_validate_uuid_valid(self):
        from facho.fe.builders.validators import validate_uuid

        errors = validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        assert len(errors) == 0

    def test_validate_uuid_invalid(self):
        from facho.fe.builders.validators import validate_uuid

        errors = validate_uuid("not-a-uuid")
        assert len(errors) > 0

    def test_validate_positive_number(self):
        from facho.fe.builders.validators import validate_positive_number

        errors = validate_positive_number(100, "Amount")
        assert len(errors) == 0

        errors = validate_positive_number(0, "Amount", allow_zero=True)
        assert len(errors) == 0

        errors = validate_positive_number(0, "Amount", allow_zero=False)
        assert len(errors) > 0

        errors = validate_positive_number(-10, "Amount")
        assert len(errors) > 0


class TestAllowanceCharge:
    """Tests para AllowanceCharge."""

    def test_create_discount(self):
        from facho.fe.builders.allowance_charge import (
            AllowanceCharge, create_discount
        )

        discount = create_discount(
            reason="Descuento comercial",
            amount=10000.0,
            reason_code="04"
        )
        assert discount.is_charge is False
        assert discount.amount == 10000.0
        assert discount.reason == "Descuento comercial"

    def test_create_charge(self):
        from facho.fe.builders.allowance_charge import create_charge

        charge = create_charge(
            reason="Flete",
            amount=5000.0,
            reason_code="01"
        )
        assert charge.is_charge is True
        assert charge.amount == 5000.0

    def test_calculate_from_percent(self):
        from facho.fe.builders.allowance_charge import AllowanceCharge

        discount = AllowanceCharge(
            is_charge=False,
            reason="10% discount",
            percent=10.0,
            base_amount=100000.0
        )
        # amount should be calculated: 100000 * 10% = 10000
        assert discount.amount == 10000.0

    def test_calculate_totals(self):
        from facho.fe.builders.allowance_charge import (
            AllowanceCharge, calculate_totals
        )

        items = [
            AllowanceCharge(is_charge=False, reason="D1", amount=1000),
            AllowanceCharge(is_charge=False, reason="D2", amount=2000),
            AllowanceCharge(is_charge=True, reason="C1", amount=500),
        ]
        discounts, charges = calculate_totals(items)
        assert discounts == 3000.0
        assert charges == 500.0


class TestConstants:
    """Tests para las nuevas constantes."""

    def test_document_type_codes(self):
        from facho.fe.builders.constants import (
            EXPORT_INVOICE_TYPE_CODE,
            CONTINGENCY_INVOICE_TYPE_CODE,
            SUPPORT_DOCUMENT_TYPE_CODE,
        )

        assert EXPORT_INVOICE_TYPE_CODE == '02'
        assert CONTINGENCY_INVOICE_TYPE_CODE == '04'
        assert SUPPORT_DOCUMENT_TYPE_CODE == '05'

    def test_incoterms(self):
        from facho.fe.builders.constants import INCOTERMS

        assert 'FOB' in INCOTERMS
        assert 'CIF' in INCOTERMS
        assert 'EXW' in INCOTERMS
        assert INCOTERMS['FOB'] == 'Free On Board'

    def test_currencies(self):
        from facho.fe.builders.constants import CURRENCIES

        assert 'USD' in CURRENCIES
        assert 'EUR' in CURRENCIES
        assert 'COP' in CURRENCIES

    def test_allowance_reason_codes(self):
        from facho.fe.builders.constants import (
            ALLOWANCE_REASON_CODES,
            CHARGE_REASON_CODES,
        )

        assert '01' in ALLOWANCE_REASON_CODES
        assert '01' in CHARGE_REASON_CODES


class TestDataClasses:
    """Tests para las nuevas data classes."""

    def test_support_document_data(self):
        from facho.fe.builders.support_document_builder import SupportDocumentData

        data = SupportDocumentData(
            number='DS0001',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
        )
        assert data.number == 'DS0001'
        assert data.payment_means_code == '10'
        # Test aliases
        assert data.supplier is None
        assert data.customer is None

    def test_export_invoice_data(self):
        from facho.fe.builders.export_invoice_builder import (
            ExportInvoiceData, DeliveryTerms, DeliveryInfo, ExchangeRate
        )

        terms = DeliveryTerms(incoterm='FOB', location='Cartagena')
        assert terms.incoterm == 'FOB'

        delivery = DeliveryInfo(country_code='US', country_name='Estados Unidos')
        assert delivery.country_code == 'US'

        exchange = ExchangeRate(source_currency='USD', rate=4000.0)
        assert exchange.rate == 4000.0
        assert exchange.target_currency == 'COP'

        data = ExportInvoiceData(
            number='EXP0001',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
            currency='USD'
        )
        assert data.currency == 'USD'

    def test_contingency_invoice_data(self):
        from facho.fe.builders.contingency_invoice_builder import (
            ContingencyInvoiceData
        )

        data = ContingencyInvoiceData(
            number='CONT0001',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00',
            contingency_date='2024-01-15',
            contingency_reason='Servicios DIAN no disponibles'
        )
        assert data.contingency_date == '2024-01-15'
        assert 'DIAN' in data.contingency_reason


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
