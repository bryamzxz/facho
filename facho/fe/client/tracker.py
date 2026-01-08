# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Sistema de tracking para documentos electronicos DIAN.
Permite rastrear documentos enviados, sus estados y consecutivos.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class TrackedDocument:
    """Documento rastreado."""
    doc_type: str  # 'factura', 'credito', 'debito'
    number: str  # Numero del documento (ej: SETP990000001)
    uuid: str  # CUFE o CUDE
    issue_date: str  # Fecha de emision
    issue_time: str = ''  # Hora de emision
    zip_key: Optional[str] = None  # ZipKey de DIAN
    is_valid: Optional[bool] = None  # Estado de validacion
    status_code: Optional[str] = None  # Codigo de estado DIAN
    status_description: Optional[str] = None  # Descripcion del estado
    total: float = 0.0  # Total del documento
    ref_invoice_number: Optional[str] = None  # Para notas: numero factura referenciada
    ref_invoice_uuid: Optional[str] = None  # Para notas: CUFE factura referenciada
    created_at: str = ''  # Timestamp de creacion del tracking
    updated_at: str = ''  # Timestamp de ultima actualizacion

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class TrackingData:
    """Datos de tracking completos."""
    facturas: List[TrackedDocument] = field(default_factory=list)
    notas_credito: List[TrackedDocument] = field(default_factory=list)
    notas_debito: List[TrackedDocument] = field(default_factory=list)
    last_consecutive: int = 0
    prefix: str = ''
    nit: str = ''
    created_at: str = ''
    updated_at: str = ''

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class DocumentTracker:
    """
    Sistema de tracking para documentos electronicos DIAN.

    Mantiene un registro persistente de todos los documentos enviados,
    sus estados y permite consultar y actualizar el estado de cada uno.

    Ejemplo de uso:
        tracker = DocumentTracker('/path/to/tracking.json')
        tracker.set_config(prefix='SETP', nit='1001186599', start_consecutive=990000000)

        # Obtener siguiente consecutivo
        consecutive = tracker.get_next_consecutive()  # 990000001

        # Registrar documento
        tracker.add_document(TrackedDocument(
            doc_type='factura',
            number='SETP990000001',
            uuid='...',
            issue_date='2024-01-15',
            zip_key='abc123'
        ))

        # Actualizar estado
        tracker.update_status('SETP990000001', is_valid=True, status_code='00')

        # Obtener documentos pendientes de verificacion
        pending = tracker.get_pending_documents()
    """

    def __init__(self, tracking_file: str = None):
        """
        Inicializar tracker.

        Args:
            tracking_file: Ruta al archivo JSON de tracking.
                          Por defecto usa /tmp/dian_tracking.json
        """
        if tracking_file is None:
            tracking_file = '/tmp/dian_tracking.json'

        self.tracking_file = Path(tracking_file)
        self._data: TrackingData = self._load()

    def _load(self) -> TrackingData:
        """Cargar datos de tracking desde archivo."""
        if not self.tracking_file.exists():
            return TrackingData()

        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            # Convertir diccionarios a TrackedDocument
            facturas = [
                TrackedDocument(**doc) if isinstance(doc, dict) else doc
                for doc in raw_data.get('facturas', [])
            ]
            notas_credito = [
                TrackedDocument(**doc) if isinstance(doc, dict) else doc
                for doc in raw_data.get('notas_credito', [])
            ]
            notas_debito = [
                TrackedDocument(**doc) if isinstance(doc, dict) else doc
                for doc in raw_data.get('notas_debito', [])
            ]

            return TrackingData(
                facturas=facturas,
                notas_credito=notas_credito,
                notas_debito=notas_debito,
                last_consecutive=raw_data.get('last_consecutive', 0),
                prefix=raw_data.get('prefix', ''),
                nit=raw_data.get('nit', ''),
                created_at=raw_data.get('created_at', ''),
                updated_at=raw_data.get('updated_at', ''),
            )
        except (json.JSONDecodeError, KeyError):
            return TrackingData()

    def _save(self):
        """Guardar datos de tracking a archivo."""
        self._data.updated_at = datetime.now().isoformat()

        # Convertir a diccionarios para JSON
        data = {
            'facturas': [asdict(doc) for doc in self._data.facturas],
            'notas_credito': [asdict(doc) for doc in self._data.notas_credito],
            'notas_debito': [asdict(doc) for doc in self._data.notas_debito],
            'last_consecutive': self._data.last_consecutive,
            'prefix': self._data.prefix,
            'nit': self._data.nit,
            'created_at': self._data.created_at,
            'updated_at': self._data.updated_at,
        }

        # Crear directorio si no existe
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def set_config(
        self,
        prefix: str = None,
        nit: str = None,
        start_consecutive: int = None
    ):
        """
        Configurar parametros del tracker.

        Args:
            prefix: Prefijo para los documentos (ej: 'SETP')
            nit: NIT del emisor
            start_consecutive: Consecutivo inicial
        """
        if prefix is not None:
            self._data.prefix = prefix
        if nit is not None:
            self._data.nit = nit
        if start_consecutive is not None and self._data.last_consecutive == 0:
            self._data.last_consecutive = start_consecutive
        self._save()

    def get_next_consecutive(self) -> int:
        """
        Obtener siguiente numero consecutivo.

        Returns:
            Siguiente numero consecutivo
        """
        self._data.last_consecutive += 1
        self._save()
        return self._data.last_consecutive

    def get_next_document_number(self) -> str:
        """
        Obtener siguiente numero de documento con prefijo.

        Returns:
            Numero de documento (ej: 'SETP990000001')
        """
        consecutive = self.get_next_consecutive()
        return f"{self._data.prefix}{consecutive}"

    def add_document(self, document: TrackedDocument):
        """
        Agregar documento al tracking.

        Args:
            document: Documento a agregar
        """
        document.updated_at = datetime.now().isoformat()

        if document.doc_type == 'factura':
            self._data.facturas.append(document)
        elif document.doc_type == 'credito':
            self._data.notas_credito.append(document)
        elif document.doc_type == 'debito':
            self._data.notas_debito.append(document)
        else:
            raise ValueError(f"Tipo de documento no soportado: {document.doc_type}")

        self._save()

    def update_status(
        self,
        document_number: str,
        is_valid: bool = None,
        status_code: str = None,
        status_description: str = None,
        zip_key: str = None
    ) -> bool:
        """
        Actualizar estado de un documento.

        Args:
            document_number: Numero del documento
            is_valid: Estado de validacion
            status_code: Codigo de estado DIAN
            status_description: Descripcion del estado
            zip_key: ZipKey de DIAN

        Returns:
            True si el documento fue encontrado y actualizado
        """
        all_docs = self._data.facturas + self._data.notas_credito + self._data.notas_debito

        for doc in all_docs:
            if doc.number == document_number:
                if is_valid is not None:
                    doc.is_valid = is_valid
                if status_code is not None:
                    doc.status_code = status_code
                if status_description is not None:
                    doc.status_description = status_description
                if zip_key is not None:
                    doc.zip_key = zip_key
                doc.updated_at = datetime.now().isoformat()
                self._save()
                return True

        return False

    def get_document(self, document_number: str) -> Optional[TrackedDocument]:
        """
        Obtener documento por numero.

        Args:
            document_number: Numero del documento

        Returns:
            TrackedDocument o None si no existe
        """
        all_docs = self._data.facturas + self._data.notas_credito + self._data.notas_debito

        for doc in all_docs:
            if doc.number == document_number:
                return doc

        return None

    def get_document_by_uuid(self, uuid: str) -> Optional[TrackedDocument]:
        """
        Obtener documento por UUID (CUFE/CUDE).

        Args:
            uuid: UUID del documento

        Returns:
            TrackedDocument o None si no existe
        """
        all_docs = self._data.facturas + self._data.notas_credito + self._data.notas_debito

        for doc in all_docs:
            if doc.uuid == uuid:
                return doc

        return None

    def get_pending_documents(self) -> List[TrackedDocument]:
        """
        Obtener documentos pendientes de verificacion.

        Returns:
            Lista de documentos que tienen ZipKey pero no estado definido
        """
        all_docs = self._data.facturas + self._data.notas_credito + self._data.notas_debito

        return [
            doc for doc in all_docs
            if doc.zip_key and doc.is_valid is None
        ]

    def get_failed_documents(self) -> List[TrackedDocument]:
        """
        Obtener documentos que fallaron validacion.

        Returns:
            Lista de documentos con is_valid=False
        """
        all_docs = self._data.facturas + self._data.notas_credito + self._data.notas_debito

        return [doc for doc in all_docs if doc.is_valid is False]

    def get_valid_documents(self) -> List[TrackedDocument]:
        """
        Obtener documentos validados exitosamente.

        Returns:
            Lista de documentos con is_valid=True
        """
        all_docs = self._data.facturas + self._data.notas_credito + self._data.notas_debito

        return [doc for doc in all_docs if doc.is_valid is True]

    def get_invoices(self) -> List[TrackedDocument]:
        """Obtener todas las facturas."""
        return list(self._data.facturas)

    def get_credit_notes(self) -> List[TrackedDocument]:
        """Obtener todas las notas credito."""
        return list(self._data.notas_credito)

    def get_debit_notes(self) -> List[TrackedDocument]:
        """Obtener todas las notas debito."""
        return list(self._data.notas_debito)

    def get_last_invoice(self) -> Optional[TrackedDocument]:
        """Obtener ultima factura enviada."""
        if self._data.facturas:
            return self._data.facturas[-1]
        return None

    def get_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen del estado de tracking.

        Returns:
            Diccionario con contadores y estadisticas
        """
        all_docs = self._data.facturas + self._data.notas_credito + self._data.notas_debito
        valid_docs = [d for d in all_docs if d.is_valid is True]
        failed_docs = [d for d in all_docs if d.is_valid is False]
        pending_docs = [d for d in all_docs if d.zip_key and d.is_valid is None]

        return {
            'total_facturas': len(self._data.facturas),
            'total_notas_credito': len(self._data.notas_credito),
            'total_notas_debito': len(self._data.notas_debito),
            'total_documentos': len(all_docs),
            'validados': len(valid_docs),
            'rechazados': len(failed_docs),
            'pendientes': len(pending_docs),
            'ultimo_consecutivo': self._data.last_consecutive,
            'prefix': self._data.prefix,
            'nit': self._data.nit,
        }

    def get_habilitacion_progress(self) -> Dict[str, Any]:
        """
        Obtener progreso para habilitacion DIAN.

        La habilitacion requiere:
        - 30 facturas
        - 10 notas credito
        - 10 notas debito

        Returns:
            Diccionario con progreso de habilitacion
        """
        valid_facturas = [d for d in self._data.facturas if d.is_valid is True]
        valid_creditos = [d for d in self._data.notas_credito if d.is_valid is True]
        valid_debitos = [d for d in self._data.notas_debito if d.is_valid is True]

        facturas_required = 30
        creditos_required = 10
        debitos_required = 10

        return {
            'facturas': {
                'completadas': len(valid_facturas),
                'requeridas': facturas_required,
                'faltantes': max(0, facturas_required - len(valid_facturas)),
                'completo': len(valid_facturas) >= facturas_required,
            },
            'notas_credito': {
                'completadas': len(valid_creditos),
                'requeridas': creditos_required,
                'faltantes': max(0, creditos_required - len(valid_creditos)),
                'completo': len(valid_creditos) >= creditos_required,
            },
            'notas_debito': {
                'completadas': len(valid_debitos),
                'requeridas': debitos_required,
                'faltantes': max(0, debitos_required - len(valid_debitos)),
                'completo': len(valid_debitos) >= debitos_required,
            },
            'habilitacion_completa': (
                len(valid_facturas) >= facturas_required and
                len(valid_creditos) >= creditos_required and
                len(valid_debitos) >= debitos_required
            ),
        }

    def clear(self):
        """Limpiar todos los datos de tracking."""
        self._data = TrackingData(
            prefix=self._data.prefix,
            nit=self._data.nit,
            last_consecutive=0,
        )
        self._save()

    def export_to_dict(self) -> Dict[str, Any]:
        """Exportar todos los datos como diccionario."""
        return {
            'facturas': [asdict(doc) for doc in self._data.facturas],
            'notas_credito': [asdict(doc) for doc in self._data.notas_credito],
            'notas_debito': [asdict(doc) for doc in self._data.notas_debito],
            'last_consecutive': self._data.last_consecutive,
            'prefix': self._data.prefix,
            'nit': self._data.nit,
            'summary': self.get_summary(),
            'habilitacion': self.get_habilitacion_progress(),
        }
