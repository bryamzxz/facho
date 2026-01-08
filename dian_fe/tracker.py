# This file is part of dian_fe.
"""
Tracking de documentos enviados a DIAN.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class DocumentTracker:
    """
    Gestiona el seguimiento de documentos enviados a DIAN.

    Almacena informacion de facturas, notas credito y notas debito
    enviados, junto con sus estados y consecutivos.
    """

    def __init__(self, path: str = '/tmp/dian_tracking.json'):
        """
        Inicializar tracker.

        Args:
            path: Ruta al archivo de tracking JSON
        """
        self.path = path
        self.data = self._load()

    def _load(self) -> Dict:
        """Cargar datos del archivo."""
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            'facturas': [],
            'notas_credito': [],
            'notas_debito': [],
            'last_consecutive': 990000000
        }

    def save(self):
        """Guardar datos al archivo."""
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def next_consecutive(self) -> int:
        """
        Obtener siguiente consecutivo.

        Returns:
            Proximo numero consecutivo
        """
        self.data['last_consecutive'] += 1
        self.save()
        return self.data['last_consecutive']

    def add_document(self, doc_type: str, doc_info: Dict):
        """
        Agregar documento al tracking.

        Args:
            doc_type: Tipo de documento ('factura', 'credito', 'debito')
            doc_info: Informacion del documento
        """
        key = {
            'factura': 'facturas',
            'credito': 'notas_credito',
            'debito': 'notas_debito'
        }.get(doc_type)

        if key:
            doc_info['timestamp'] = datetime.now().isoformat()
            self.data[key].append(doc_info)
            self.save()

    def get_documents(self, doc_type: str) -> List[Dict]:
        """
        Obtener documentos por tipo.

        Args:
            doc_type: Tipo de documento

        Returns:
            Lista de documentos
        """
        key = {
            'factura': 'facturas',
            'credito': 'notas_credito',
            'debito': 'notas_debito'
        }.get(doc_type)

        return self.data.get(key, []) if key else []

    def get_document_by_number(self, number: str) -> Optional[Dict]:
        """
        Buscar documento por numero.

        Args:
            number: Numero del documento

        Returns:
            Documento encontrado o None
        """
        for key in ['facturas', 'notas_credito', 'notas_debito']:
            for doc in self.data.get(key, []):
                if doc.get('number') == number:
                    return doc
        return None

    def get_invoice_for_reference(self, index: int = 0) -> Optional[Dict]:
        """
        Obtener factura para usar como referencia en notas.

        Args:
            index: Indice de la factura (0 = primera)

        Returns:
            Informacion de la factura o None
        """
        facturas = self.data.get('facturas', [])
        if index < len(facturas):
            return facturas[index]
        return None

    def get_summary(self) -> Dict:
        """
        Obtener resumen de documentos.

        Returns:
            Diccionario con conteos
        """
        return {
            'facturas': len(self.data.get('facturas', [])),
            'notas_credito': len(self.data.get('notas_credito', [])),
            'notas_debito': len(self.data.get('notas_debito', [])),
            'last_consecutive': self.data.get('last_consecutive', 0)
        }

    def clear(self):
        """Limpiar todos los documentos."""
        self.data = {
            'facturas': [],
            'notas_credito': [],
            'notas_debito': [],
            'last_consecutive': 990000000
        }
        self.save()
