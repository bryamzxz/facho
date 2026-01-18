# Tests for the improvements to Facho

"""
Tests para las mejoras realizadas a Facho:
- CUFE/CUDE/CUDS calculator
- Nuevas excepciones
- Validaciones de produccion
- Constantes adicionales
- Metodos de conveniencia en Tax
"""

import pytest
from datetime import datetime


class TestCufeCalculator:
    """Tests para el calculador CUFE/CUDE/CUDS."""

    def test_cufe_format(self):
        """CUFE debe tener 96 caracteres hexadecimales."""
        from facho.fe.builders.cufe import CufeInput, calculate_cufe

        data = CufeInput(
            number='SETP990000001',
            issue_date='2026-01-18',
            issue_time='10:30:00-05:00',
            subtotal=100000.00,
            iva_amount=19000.00,
            total=119000.00,
            supplier_nit='1001186599',
            customer_nit='222222222222',
            technical_key='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            environment='2'
        )
        cufe = calculate_cufe(data)

        assert len(cufe) == 96
        assert cufe.isalnum()
        assert all(c in '0123456789abcdef' for c in cufe.lower())

    def test_cude_format(self):
        """CUDE debe tener 96 caracteres hexadecimales."""
        from facho.fe.builders.cufe import CufeInput, calculate_cude

        data = CufeInput(
            number='NC1',
            issue_date='2026-01-18',
            issue_time='10:30:00-05:00',
            subtotal=50000.00,
            iva_amount=9500.00,
            total=59500.00,
            supplier_nit='1001186599',
            customer_nit='222222222222',
            technical_key='12345',  # PIN para CUDE
            environment='2'
        )
        cude = calculate_cude(data)

        assert len(cude) == 96
        assert cude.isalnum()

    def test_truncar_no_redondea(self):
        """DIAN trunca, no redondea."""
        from facho.fe.builders.taxes import truncar

        assert truncar(123.456, 2) == 123.45
        assert truncar(123.999, 2) == 123.99
        assert truncar(99.995, 2) == 99.99  # NO 100.00
        assert truncar(0.999, 2) == 0.99

    def test_format_amount(self):
        """format_amount debe truncar correctamente."""
        from facho.fe.builders.cufe import format_amount

        assert format_amount(123.456) == '123.45'
        assert format_amount(99.999) == '99.99'
        assert format_amount(100000.00) == '100000.00'

    def test_software_security_code(self):
        """SoftwareSecurityCode debe tener 96 caracteres."""
        from facho.fe.builders.cufe import calculate_software_security_code

        code = calculate_software_security_code(
            software_id='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
            software_pin='12345',
            doc_number='SETP990000001'
        )

        assert len(code) == 96
        assert code.isalnum()

    def test_verify_cufe(self):
        """verify_cufe debe validar correctamente."""
        from facho.fe.builders.cufe import CufeInput, calculate_cufe, verify_cufe

        data = CufeInput(
            number='TEST1',
            issue_date='2026-01-18',
            issue_time='10:30:00-05:00',
            subtotal=1000.00,
            iva_amount=190.00,
            total=1190.00,
            supplier_nit='123456789',
            customer_nit='987654321',
            technical_key='test_key',
            environment='2'
        )
        cufe = calculate_cufe(data)

        assert verify_cufe(cufe, data) is True
        assert verify_cufe('invalid', data) is False

    def test_uuid_type_by_doc(self):
        """get_uuid_type debe retornar el tipo correcto."""
        from facho.fe.builders.cufe import get_uuid_type

        assert get_uuid_type('01') == 'CUFE-SHA384'  # Factura
        assert get_uuid_type('02') == 'CUFE-SHA384'  # Exportacion
        assert get_uuid_type('03') == 'CUDE-SHA384'  # POS
        assert get_uuid_type('04') == 'CUFE-SHA384'  # Contingencia
        assert get_uuid_type('05') == 'CUDS-SHA384'  # Doc soporte
        assert get_uuid_type('91') == 'CUDE-SHA384'  # Nota credito
        assert get_uuid_type('92') == 'CUDE-SHA384'  # Nota debito


class TestTaxMethods:
    """Tests para metodos de conveniencia de Tax."""

    def test_from_line(self):
        """Tax.from_line debe crear impuesto correcto."""
        from facho.fe.builders.taxes import Tax

        tax = Tax.from_line(100000.0, '01', 19.0)

        assert tax.code == '01'
        assert tax.percent == 19.0
        assert tax.taxable_amount == 100000.0
        assert tax.amount == 19000.0

    def test_no_iva(self):
        """Tax.no_iva debe crear IVA 0%."""
        from facho.fe.builders.taxes import Tax

        tax = Tax.no_iva(50000.0)

        assert tax.code == '01'
        assert tax.percent == 0.0
        assert tax.amount == 0.0
        assert tax.is_withholding is False

    def test_inc_8(self):
        """Tax.inc_8 debe crear INC 8%."""
        from facho.fe.builders.taxes import Tax

        tax = Tax.inc_8(100000.0)

        assert tax.code == '04'
        assert tax.percent == 8.0
        assert tax.amount == 8000.0

    def test_inc_16(self):
        """Tax.inc_16 debe crear INC 16%."""
        from facho.fe.builders.taxes import Tax

        tax = Tax.inc_16(100000.0)

        assert tax.code == '04'
        assert tax.percent == 16.0
        assert tax.amount == 16000.0

    def test_to_dict_from_dict(self):
        """Tax.to_dict y Tax.from_dict deben ser inversos."""
        from facho.fe.builders.taxes import Tax

        original = Tax.iva_19(100000.0)
        data = original.to_dict()
        restored = Tax.from_dict(data)

        assert restored.code == original.code
        assert restored.percent == original.percent
        assert restored.taxable_amount == original.taxable_amount
        assert restored.amount == original.amount

    def test_export_exempt(self):
        """Tax.export_exempt debe crear IVA exento."""
        from facho.fe.builders.taxes import Tax

        tax = Tax.export_exempt(100000.0)

        assert tax.code == '06'
        assert tax.percent == 0.0
        assert tax.amount == 0.0


class TestCreditNoteReference:
    """Tests para referencia de nota credito."""

    def test_credit_note_reference_validation(self):
        """Validar referencia de nota credito."""
        from facho.fe.builders.validators import validate_credit_note_reference

        errors = validate_credit_note_reference(
            invoice_number='SETP990000001',
            invoice_cufe='a' * 96,
            invoice_date='2026-01-15',
            response_code='2'
        )

        assert errors == []

    def test_credit_note_invalid_cufe(self):
        """CUFE invalido debe dar error."""
        from facho.fe.builders.validators import validate_credit_note_reference

        errors = validate_credit_note_reference(
            invoice_number='SETP990000001',
            invoice_cufe='invalid',
            invoice_date='2026-01-15',
            response_code='2'
        )

        assert len(errors) > 0
        assert any('96' in e for e in errors)

    def test_credit_note_invalid_response_code(self):
        """Codigo de respuesta invalido debe dar error."""
        from facho.fe.builders.validators import validate_credit_note_reference

        errors = validate_credit_note_reference(
            invoice_number='SETP990000001',
            invoice_cufe='a' * 96,
            invoice_date='2026-01-15',
            response_code='99'  # Invalido
        )

        assert len(errors) > 0


class TestDebitNoteReference:
    """Tests para referencia de nota debito."""

    def test_debit_note_response_codes(self):
        """Codigos de respuesta nota debito."""
        from facho.fe.builders.constants import DEBIT_NOTE_RESPONSE_CODES

        assert DEBIT_NOTE_RESPONSE_CODES['1'] == 'Intereses'
        assert DEBIT_NOTE_RESPONSE_CODES['2'] == 'Gastos por cobrar'
        assert DEBIT_NOTE_RESPONSE_CODES['3'] == 'Cambio del valor'
        assert DEBIT_NOTE_RESPONSE_CODES['4'] == 'Otros'


class TestDocTypes:
    """Tests para DOC_TYPES_FULL."""

    def test_all_doc_types_have_required_fields(self):
        """Todos los tipos de documento deben tener campos requeridos."""
        from facho.fe.builders.constants import DOC_TYPES_FULL

        required_fields = ['code', 'root_element', 'namespace', 'uuid_scheme']

        for doc_key, doc_type in DOC_TYPES_FULL.items():
            for field in required_fields:
                assert field in doc_type, f"{doc_key} missing {field}"

    def test_debit_note_uses_requested_monetary_total(self):
        """Nota debito usa RequestedMonetaryTotal, no LegalMonetaryTotal."""
        from facho.fe.builders.constants import DOC_TYPES_FULL

        nd_type = DOC_TYPES_FULL['ND']
        assert nd_type.get('total_element') == 'RequestedMonetaryTotal'

    def test_credit_note_uses_cude(self):
        """Nota credito debe usar CUDE, no CUFE."""
        from facho.fe.builders.constants import DOC_TYPES_FULL

        nc_type = DOC_TYPES_FULL['NC']
        assert nc_type['uuid_scheme'] == 'CUDE-SHA384'
        assert nc_type['uses_technical_key'] is False

    def test_support_document_uses_cuds(self):
        """Documento soporte usa CUDS."""
        from facho.fe.builders.constants import DOC_TYPES_FULL

        ds_type = DOC_TYPES_FULL['DS']
        assert ds_type['uuid_scheme'] == 'CUDS-SHA384'
        assert ds_type['code'] == '05'
        assert 'documento soporte' in ds_type['profile_id'].lower()


class TestPosDocument:
    """Tests para documento POS."""

    def test_pos_uvt_limit(self):
        """Limite de 5 UVT para documento POS."""
        from facho.fe.builders.pos_document_builder import POS_UVT_LIMIT

        assert POS_UVT_LIMIT == 5

    def test_generic_consumer(self):
        """Consumidor final generico."""
        from facho.fe.builders.constants import GENERIC_CONSUMER

        assert GENERIC_CONSUMER['nit'] == '222222222222'
        assert GENERIC_CONSUMER['name'] == 'CONSUMIDOR FINAL'

    def test_uvt_values(self):
        """Valores UVT deben estar definidos."""
        from facho.fe.builders.constants import UVT_VALUES

        assert 2024 in UVT_VALUES
        assert 2025 in UVT_VALUES
        assert UVT_VALUES[2024] > 40000

    def test_pos_max_value(self):
        """Valor maximo POS debe calcularse correctamente."""
        from facho.fe.builders.pos_document_builder import PosDocumentData

        data = PosDocumentData(
            number='POS001',
            issue_date='2024-01-15',
            issue_time='10:30:00-05:00'
        )

        max_value = data.get_max_value(2024)
        uvt_2024 = data.get_uvt_value(2024)

        assert max_value == 5 * uvt_2024


class TestValidations:
    """Tests para validaciones de produccion."""

    def test_validate_resolution_dates_valid(self):
        """Fecha dentro de resolucion debe pasar."""
        from facho.fe.builders.validators import validate_resolution_dates

        errors = validate_resolution_dates(
            start_date='2024-01-01',
            end_date='2024-12-31',
            issue_date='2024-06-15'
        )

        assert errors == []

    def test_validate_resolution_dates_before_start(self):
        """Fecha anterior a inicio debe fallar."""
        from facho.fe.builders.validators import validate_resolution_dates

        errors = validate_resolution_dates(
            start_date='2024-01-01',
            end_date='2024-12-31',
            issue_date='2023-12-31'
        )

        assert len(errors) > 0
        assert any('anterior' in e for e in errors)

    def test_validate_resolution_dates_after_end(self):
        """Fecha posterior a fin debe fallar."""
        from facho.fe.builders.validators import validate_resolution_dates

        errors = validate_resolution_dates(
            start_date='2024-01-01',
            end_date='2024-12-31',
            issue_date='2025-01-01'
        )

        assert len(errors) > 0
        assert any('posterior' in e for e in errors)

    def test_validate_cufe_format_valid(self):
        """CUFE valido debe pasar."""
        from facho.fe.builders.validators import validate_cufe_format

        errors = validate_cufe_format('a' * 96)
        assert errors == []

    def test_validate_cufe_format_invalid_length(self):
        """CUFE con longitud incorrecta debe fallar."""
        from facho.fe.builders.validators import validate_cufe_format

        errors = validate_cufe_format('abcd')
        assert len(errors) > 0
        assert any('96' in e for e in errors)

    def test_validate_consecutive_in_range(self):
        """Consecutivo en rango debe pasar."""
        from facho.fe.builders.validators import validate_consecutive_in_range

        errors = validate_consecutive_in_range(500, 1, 1000)
        assert errors == []

    def test_validate_consecutive_below_range(self):
        """Consecutivo debajo del rango debe fallar."""
        from facho.fe.builders.validators import validate_consecutive_in_range

        errors = validate_consecutive_in_range(0, 1, 1000)
        assert len(errors) > 0

    def test_validate_totals_correct(self):
        """Totales correctos deben pasar."""
        from facho.fe.builders.validators import validate_totals

        errors = validate_totals(
            line_extension=100000.0,
            tax_exclusive=100000.0,
            tax_inclusive=119000.0,
            tax_amount=19000.0,
            payable_amount=119000.0
        )

        assert errors == []

    def test_validate_totals_incorrect(self):
        """Totales incorrectos deben fallar."""
        from facho.fe.builders.validators import validate_totals

        errors = validate_totals(
            line_extension=100000.0,
            tax_exclusive=100000.0,
            tax_inclusive=120000.0,  # Deberia ser 119000
            tax_amount=19000.0,
            payable_amount=120000.0
        )

        assert len(errors) > 0

    def test_validate_pos_limits(self):
        """Limite POS debe validarse."""
        from facho.fe.builders.validators import validate_pos_limits

        # Total dentro del limite
        errors = validate_pos_limits(200000.0, 5, 47065.0)
        assert errors == []

        # Total fuera del limite
        errors = validate_pos_limits(500000.0, 5, 47065.0)
        assert len(errors) > 0


class TestExceptions:
    """Tests para nuevas excepciones."""

    def test_duplicate_invoice_error(self):
        """DuplicateInvoiceError debe tener datos correctos."""
        from facho.fe.builders.exceptions import DuplicateInvoiceError

        error = DuplicateInvoiceError('SETP990000001', 'cufe123')

        assert error.invoice_number == 'SETP990000001'
        assert error.existing_cufe == 'cufe123'
        assert 'SETP990000001' in str(error)

    def test_resolution_expired_error(self):
        """ResolutionExpiredError debe tener datos correctos."""
        from facho.fe.builders.exceptions import ResolutionExpiredError

        error = ResolutionExpiredError('18764000001234', '2023-12-31')

        assert error.resolution_number == '18764000001234'
        assert error.end_date == '2023-12-31'

    def test_uvt_limit_exceeded_error(self):
        """UvtLimitExceededError debe calcular max_value."""
        from facho.fe.builders.exceptions import UvtLimitExceededError

        error = UvtLimitExceededError(
            total=500000.0,
            uvt_limit=5,
            uvt_value=47065.0
        )

        assert error.total == 500000.0
        assert error.uvt_limit == 5
        assert error.max_value == 5 * 47065.0

    def test_create_dian_exception(self):
        """create_dian_exception debe crear excepcion correcta."""
        from facho.fe.builders.exceptions import create_dian_exception

        error = create_dian_exception('ZE04', 'Certificado vencido')

        assert error.code == 'ZE04'


class TestConstants:
    """Tests para nuevas constantes."""

    def test_dian_endpoints(self):
        """Endpoints DIAN deben estar definidos."""
        from facho.fe.builders.constants import DIAN_ENDPOINTS

        assert 'produccion' in DIAN_ENDPOINTS
        assert 'habilitacion' in DIAN_ENDPOINTS
        assert 'vpfe.dian.gov.co' in DIAN_ENDPOINTS['produccion']
        assert 'vpfe-hab.dian.gov.co' in DIAN_ENDPOINTS['habilitacion']

    def test_ns_soap(self):
        """Namespaces SOAP deben estar definidos."""
        from facho.fe.builders.constants import NS_SOAP

        assert 'soap' in NS_SOAP
        assert 'wsse' in NS_SOAP
        assert 'wsu' in NS_SOAP
        assert 'ds' in NS_SOAP

    def test_signature_algorithms(self):
        """Algoritmos de firma deben estar definidos."""
        from facho.fe.builders.constants import (
            C14N_ALG, C14N_EXC_ALG, RSA_SHA256, SHA256_ALG
        )

        assert 'xml-c14n' in C14N_ALG
        assert 'xml-exc-c14n' in C14N_EXC_ALG
        assert 'rsa-sha256' in RSA_SHA256
        assert 'sha256' in SHA256_ALG

    def test_politica_firma(self):
        """Politica de firma DIAN debe estar definida."""
        from facho.fe.builders.constants import POLITICA_URL, POLITICA_HASH

        assert 'dian.gov.co' in POLITICA_URL
        assert len(POLITICA_HASH) > 0

    def test_tax_regimes(self):
        """Regimenes fiscales deben estar definidos."""
        from facho.fe.builders.constants import TAX_REGIMES

        assert TAX_REGIMES['RESPONSABLE_IVA'] == '48'
        assert TAX_REGIMES['NO_RESPONSABLE_IVA'] == '49'
        assert TAX_REGIMES['NO_RESPONSABLE_PN'] == 'R-99-PN'

    def test_id_types(self):
        """Tipos de identificacion deben estar definidos."""
        from facho.fe.builders.constants import ID_TYPES

        assert ID_TYPES['31'] == 'NIT'
        assert ID_TYPES['13'] == 'Cedula de ciudadania'
        assert ID_TYPES['41'] == 'Pasaporte'
