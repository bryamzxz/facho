#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Tests para el sistema de tracking de documentos DIAN.
"""

import pytest
import os
import json
import tempfile
from datetime import datetime

# Importar directamente del modulo para evitar dependencias legacy
from facho.fe.client.tracker import DocumentTracker, TrackedDocument, TrackingData


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_tracking_file():
    """Archivo temporal para tracking."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def tracker(temp_tracking_file):
    """Tracker con archivo temporal."""
    return DocumentTracker(temp_tracking_file)


@pytest.fixture
def sample_invoice():
    """Factura de ejemplo."""
    return TrackedDocument(
        doc_type='factura',
        number='SETP990000001',
        uuid='a' * 96,
        issue_date='2024-01-15',
        issue_time='10:30:00-05:00',
        total=119000.0,
        zip_key='abc123',
    )


@pytest.fixture
def sample_credit_note():
    """Nota credito de ejemplo."""
    return TrackedDocument(
        doc_type='credito',
        number='SETP990000002',
        uuid='b' * 96,
        issue_date='2024-01-16',
        issue_time='11:00:00-05:00',
        total=50000.0,
        ref_invoice_number='SETP990000001',
        ref_invoice_uuid='a' * 96,
        zip_key='def456',
    )


@pytest.fixture
def sample_debit_note():
    """Nota debito de ejemplo."""
    return TrackedDocument(
        doc_type='debito',
        number='SETP990000003',
        uuid='c' * 96,
        issue_date='2024-01-17',
        issue_time='09:00:00-05:00',
        total=25000.0,
        ref_invoice_number='SETP990000001',
        ref_invoice_uuid='a' * 96,
        zip_key='ghi789',
    )


# =============================================================================
# TESTS DE TRACKED DOCUMENT
# =============================================================================

class TestTrackedDocument:
    """Tests para TrackedDocument."""

    def test_create_document(self, sample_invoice):
        """Test crear documento."""
        assert sample_invoice.doc_type == 'factura'
        assert sample_invoice.number == 'SETP990000001'
        assert sample_invoice.uuid == 'a' * 96

    def test_document_has_timestamps(self):
        """Test que documento tenga timestamps."""
        doc = TrackedDocument(
            doc_type='factura',
            number='TEST001',
            uuid='x' * 96,
            issue_date='2024-01-15',
        )
        assert doc.created_at != ''
        assert doc.updated_at != ''

    def test_document_optional_fields(self):
        """Test campos opcionales de documento."""
        doc = TrackedDocument(
            doc_type='factura',
            number='TEST001',
            uuid='x' * 96,
            issue_date='2024-01-15',
        )
        assert doc.zip_key is None
        assert doc.is_valid is None
        assert doc.status_code is None


# =============================================================================
# TESTS DE DOCUMENT TRACKER - CONFIGURACION
# =============================================================================

class TestDocumentTrackerConfig:
    """Tests para configuracion del tracker."""

    def test_create_tracker(self, temp_tracking_file):
        """Test crear tracker."""
        tracker = DocumentTracker(temp_tracking_file)
        assert tracker is not None

    def test_set_config(self, tracker):
        """Test configurar tracker."""
        tracker.set_config(prefix='SETP', nit='1001186599', start_consecutive=990000000)
        summary = tracker.get_summary()

        assert summary['prefix'] == 'SETP'
        assert summary['nit'] == '1001186599'

    def test_persistence(self, temp_tracking_file):
        """Test que datos persistan."""
        # Crear tracker y agregar documento
        tracker1 = DocumentTracker(temp_tracking_file)
        tracker1.set_config(prefix='TEST', nit='123456789')
        tracker1.add_document(TrackedDocument(
            doc_type='factura',
            number='TEST001',
            uuid='x' * 96,
            issue_date='2024-01-15',
        ))

        # Crear nuevo tracker y verificar datos
        tracker2 = DocumentTracker(temp_tracking_file)
        summary = tracker2.get_summary()

        assert summary['prefix'] == 'TEST'
        assert summary['total_facturas'] == 1


# =============================================================================
# TESTS DE DOCUMENT TRACKER - CONSECUTIVOS
# =============================================================================

class TestDocumentTrackerConsecutives:
    """Tests para gestion de consecutivos."""

    def test_get_next_consecutive(self, tracker):
        """Test obtener siguiente consecutivo."""
        tracker.set_config(start_consecutive=100)

        c1 = tracker.get_next_consecutive()
        c2 = tracker.get_next_consecutive()

        assert c1 == 101
        assert c2 == 102

    def test_get_next_document_number(self, tracker):
        """Test obtener siguiente numero de documento."""
        tracker.set_config(prefix='SETP', start_consecutive=990000000)

        num = tracker.get_next_document_number()
        assert num == 'SETP990000001'


# =============================================================================
# TESTS DE DOCUMENT TRACKER - DOCUMENTOS
# =============================================================================

class TestDocumentTrackerDocuments:
    """Tests para gestion de documentos."""

    def test_add_invoice(self, tracker, sample_invoice):
        """Test agregar factura."""
        tracker.add_document(sample_invoice)

        invoices = tracker.get_invoices()
        assert len(invoices) == 1
        assert invoices[0].number == 'SETP990000001'

    def test_add_credit_note(self, tracker, sample_credit_note):
        """Test agregar nota credito."""
        tracker.add_document(sample_credit_note)

        notes = tracker.get_credit_notes()
        assert len(notes) == 1
        assert notes[0].number == 'SETP990000002'

    def test_add_debit_note(self, tracker, sample_debit_note):
        """Test agregar nota debito."""
        tracker.add_document(sample_debit_note)

        notes = tracker.get_debit_notes()
        assert len(notes) == 1
        assert notes[0].number == 'SETP990000003'

    def test_get_document_by_number(self, tracker, sample_invoice):
        """Test obtener documento por numero."""
        tracker.add_document(sample_invoice)

        doc = tracker.get_document('SETP990000001')
        assert doc is not None
        assert doc.uuid == 'a' * 96

    def test_get_document_not_found(self, tracker):
        """Test documento no encontrado."""
        doc = tracker.get_document('NOTEXIST')
        assert doc is None

    def test_get_document_by_uuid(self, tracker, sample_invoice):
        """Test obtener documento por UUID."""
        tracker.add_document(sample_invoice)

        doc = tracker.get_document_by_uuid('a' * 96)
        assert doc is not None
        assert doc.number == 'SETP990000001'


# =============================================================================
# TESTS DE DOCUMENT TRACKER - ACTUALIZACION DE ESTADO
# =============================================================================

class TestDocumentTrackerStatus:
    """Tests para actualizacion de estado."""

    def test_update_status(self, tracker, sample_invoice):
        """Test actualizar estado."""
        tracker.add_document(sample_invoice)

        result = tracker.update_status(
            'SETP990000001',
            is_valid=True,
            status_code='00',
            status_description='Procesado correctamente'
        )

        assert result is True
        doc = tracker.get_document('SETP990000001')
        assert doc.is_valid is True
        assert doc.status_code == '00'

    def test_update_status_not_found(self, tracker):
        """Test actualizar documento no encontrado."""
        result = tracker.update_status('NOTEXIST', is_valid=True)
        assert result is False

    def test_get_pending_documents(self, tracker, sample_invoice, sample_credit_note):
        """Test obtener documentos pendientes."""
        tracker.add_document(sample_invoice)
        tracker.add_document(sample_credit_note)

        # Marcar uno como validado
        tracker.update_status('SETP990000001', is_valid=True)

        pending = tracker.get_pending_documents()
        assert len(pending) == 1
        assert pending[0].number == 'SETP990000002'

    def test_get_valid_documents(self, tracker, sample_invoice, sample_credit_note):
        """Test obtener documentos validados."""
        tracker.add_document(sample_invoice)
        tracker.add_document(sample_credit_note)

        tracker.update_status('SETP990000001', is_valid=True)
        tracker.update_status('SETP990000002', is_valid=False)

        valid = tracker.get_valid_documents()
        assert len(valid) == 1
        assert valid[0].number == 'SETP990000001'

    def test_get_failed_documents(self, tracker, sample_invoice, sample_credit_note):
        """Test obtener documentos rechazados."""
        tracker.add_document(sample_invoice)
        tracker.add_document(sample_credit_note)

        tracker.update_status('SETP990000001', is_valid=True)
        tracker.update_status('SETP990000002', is_valid=False)

        failed = tracker.get_failed_documents()
        assert len(failed) == 1
        assert failed[0].number == 'SETP990000002'


# =============================================================================
# TESTS DE DOCUMENT TRACKER - RESUMEN Y HABILITACION
# =============================================================================

class TestDocumentTrackerSummary:
    """Tests para resumen y progreso de habilitacion."""

    def test_get_summary(self, tracker, sample_invoice, sample_credit_note, sample_debit_note):
        """Test obtener resumen."""
        tracker.set_config(prefix='SETP', nit='1001186599')
        tracker.add_document(sample_invoice)
        tracker.add_document(sample_credit_note)
        tracker.add_document(sample_debit_note)

        summary = tracker.get_summary()

        assert summary['total_facturas'] == 1
        assert summary['total_notas_credito'] == 1
        assert summary['total_notas_debito'] == 1
        assert summary['total_documentos'] == 3
        assert summary['prefix'] == 'SETP'

    def test_get_habilitacion_progress_empty(self, tracker):
        """Test progreso habilitacion vacio."""
        progress = tracker.get_habilitacion_progress()

        assert progress['facturas']['completadas'] == 0
        assert progress['facturas']['requeridas'] == 30
        assert progress['facturas']['faltantes'] == 30
        assert progress['habilitacion_completa'] is False

    def test_get_habilitacion_progress_partial(self, tracker, sample_invoice):
        """Test progreso habilitacion parcial."""
        tracker.add_document(sample_invoice)
        tracker.update_status('SETP990000001', is_valid=True)

        progress = tracker.get_habilitacion_progress()

        assert progress['facturas']['completadas'] == 1
        assert progress['facturas']['faltantes'] == 29
        assert progress['habilitacion_completa'] is False

    def test_get_last_invoice(self, tracker):
        """Test obtener ultima factura."""
        for i in range(3):
            tracker.add_document(TrackedDocument(
                doc_type='factura',
                number=f'SETP00000000{i}',
                uuid='x' * 96,
                issue_date='2024-01-15',
            ))

        last = tracker.get_last_invoice()
        assert last.number == 'SETP000000002'


# =============================================================================
# TESTS DE DOCUMENT TRACKER - OPERACIONES
# =============================================================================

class TestDocumentTrackerOperations:
    """Tests para operaciones adicionales."""

    def test_clear(self, tracker, sample_invoice):
        """Test limpiar datos."""
        tracker.set_config(prefix='SETP', nit='123')
        tracker.add_document(sample_invoice)

        tracker.clear()

        summary = tracker.get_summary()
        assert summary['total_documentos'] == 0
        assert summary['prefix'] == 'SETP'  # Se mantiene config

    def test_export_to_dict(self, tracker, sample_invoice):
        """Test exportar a diccionario."""
        tracker.set_config(prefix='SETP', nit='123')
        tracker.add_document(sample_invoice)

        data = tracker.export_to_dict()

        assert 'facturas' in data
        assert 'notas_credito' in data
        assert 'notas_debito' in data
        assert 'summary' in data
        assert 'habilitacion' in data
        assert len(data['facturas']) == 1


# =============================================================================
# TESTS DE INVALID DOC TYPE
# =============================================================================

class TestDocumentTrackerErrors:
    """Tests para manejo de errores."""

    def test_invalid_doc_type(self, tracker):
        """Test tipo de documento invalido."""
        doc = TrackedDocument(
            doc_type='invalido',
            number='TEST001',
            uuid='x' * 96,
            issue_date='2024-01-15',
        )

        with pytest.raises(ValueError) as exc_info:
            tracker.add_document(doc)

        assert 'no soportado' in str(exc_info.value)
