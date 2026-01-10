# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""
Cliente DIAN simplificado con WS-Security manual.
Implementacion pura sin dependencias de zeep.
Basado en implementacion funcional aprobada por DIAN.
"""

import uuid
import base64
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

import requests
from lxml import etree

from ..signing.certificate import cert_to_base64, load_certificate, load_certificate_from_bytes
from ..signing.utils import sha256_digest, sign_data


# =============================================================================
# NAMESPACES SOAP
# =============================================================================

NS_SOAP = {
    'soap': 'http://www.w3.org/2003/05/soap-envelope',
    'wcf': 'http://wcf.dian.colombia',
    'wsa': 'http://www.w3.org/2005/08/addressing',
    'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
    'wsu': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd',
    'ec': 'http://www.w3.org/2001/10/xml-exc-c14n#',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
}

# Algoritmos
C14N_EXC_ALG = 'http://www.w3.org/2001/10/xml-exc-c14n#'
RSA_SHA256 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
SHA256_ALG = 'http://www.w3.org/2001/04/xmlenc#sha256'

# Endpoints DIAN
ENDPOINT_HABILITACION = 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc'
ENDPOINT_PRODUCCION = 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc'


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DianResponse:
    """Respuesta base de DIAN."""
    is_valid: Optional[bool] = None
    status_code: Optional[str] = None
    status_description: Optional[str] = None
    status_message: Optional[str] = None
    error_messages: Optional[list] = None
    xml_response: Optional[str] = None


@dataclass
class SendTestSetResponse(DianResponse):
    """Respuesta de SendTestSetAsync."""
    zip_key: Optional[str] = None


@dataclass
class GetStatusZipResponse(DianResponse):
    """Respuesta de GetStatusZip."""
    pass


@dataclass
class SendBillSyncResponse(DianResponse):
    """Respuesta de SendBillSync."""
    pass


# =============================================================================
# CLIENTE DIAN
# =============================================================================

class DianSimpleClient:
    """
    Cliente simplificado para servicios web DIAN.

    Implementa WS-Security manual sin dependencias externas de SOAP.
    Compatible con ambiente de habilitacion y produccion.
    """

    def __init__(
        self,
        certificate_path: str = None,
        certificate_password: str = None,
        certificate_bytes: bytes = None,
        environment: str = 'habilitacion'
    ):
        """
        Inicializar cliente DIAN.

        Args:
            certificate_path: Ruta al archivo .pfx o .p12
            certificate_password: Contrasena del certificado
            certificate_bytes: Bytes del certificado (alternativa a certificate_path)
            environment: 'habilitacion' o 'produccion'
        """
        if certificate_bytes:
            self.private_key, self.certificate, self.chain = load_certificate_from_bytes(
                certificate_bytes, certificate_password
            )
        elif certificate_path:
            self.private_key, self.certificate, self.chain = load_certificate(
                certificate_path, certificate_password
            )
        else:
            raise ValueError("Se requiere certificate_path o certificate_bytes")

        self.cert_b64 = cert_to_base64(self.certificate)
        self.environment = environment
        self.endpoint = ENDPOINT_HABILITACION if environment == 'habilitacion' else ENDPOINT_PRODUCCION
        self.timeout = 60

    def send_test_set_async(
        self,
        file_name: str,
        content_file: bytes,
        test_set_id: str
    ) -> SendTestSetResponse:
        """
        Enviar documento de prueba a DIAN (SendTestSetAsync).

        Args:
            file_name: Nombre del archivo ZIP
            content_file: Contenido del archivo ZIP en bytes
            test_set_id: ID del set de pruebas DIAN

        Returns:
            SendTestSetResponse con el ZipKey si fue exitoso
        """
        content_b64 = base64.b64encode(content_file).decode('utf-8')

        body = f'''<wcf:SendTestSetAsync xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:fileName>{file_name}</wcf:fileName>
<wcf:contentFile>{content_b64}</wcf:contentFile>
<wcf:testSetId>{test_set_id}</wcf:testSetId>
</wcf:SendTestSetAsync>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendTestSetAsync'
        response = self._send_soap_request(body, action)

        return self._parse_send_test_set_response(response)

    def send_bill_sync(
        self,
        file_name: str,
        content_file: bytes
    ) -> SendBillSyncResponse:
        """
        Enviar documento sincronicamente a DIAN (SendBillSync).

        Args:
            file_name: Nombre del archivo ZIP
            content_file: Contenido del archivo ZIP en bytes

        Returns:
            SendBillSyncResponse con el resultado
        """
        content_b64 = base64.b64encode(content_file).decode('utf-8')

        body = f'''<wcf:SendBillSync xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:fileName>{file_name}</wcf:fileName>
<wcf:contentFile>{content_b64}</wcf:contentFile>
</wcf:SendBillSync>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendBillSync'
        response = self._send_soap_request(body, action)

        return self._parse_status_response(response, SendBillSyncResponse)

    def send_bill_async(
        self,
        file_name: str,
        content_file: bytes
    ) -> SendTestSetResponse:
        """
        Enviar documento asincronicamente a DIAN (SendBillAsync).

        Args:
            file_name: Nombre del archivo ZIP
            content_file: Contenido del archivo ZIP en bytes

        Returns:
            SendTestSetResponse con el ZipKey si fue exitoso
        """
        content_b64 = base64.b64encode(content_file).decode('utf-8')

        body = f'''<wcf:SendBillAsync xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:fileName>{file_name}</wcf:fileName>
<wcf:contentFile>{content_b64}</wcf:contentFile>
</wcf:SendBillAsync>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendBillAsync'
        response = self._send_soap_request(body, action)

        return self._parse_send_test_set_response(response)

    def get_status_zip(self, track_id: str) -> GetStatusZipResponse:
        """
        Consultar estado de documento por TrackId/ZipKey (GetStatusZip).

        Args:
            track_id: TrackId o ZipKey del documento

        Returns:
            GetStatusZipResponse con el estado
        """
        body = f'''<wcf:GetStatusZip xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:trackId>{track_id}</wcf:trackId>
</wcf:GetStatusZip>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/GetStatusZip'
        response = self._send_soap_request(body, action)

        return self._parse_status_response(response, GetStatusZipResponse)

    def get_status(self, track_id: str) -> GetStatusZipResponse:
        """
        Consultar estado de documento por TrackId (GetStatus).

        Args:
            track_id: TrackId del documento (CUFE/CUDE)

        Returns:
            GetStatusZipResponse con el estado
        """
        body = f'''<wcf:GetStatus xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:trackId>{track_id}</wcf:trackId>
</wcf:GetStatus>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/GetStatus'
        response = self._send_soap_request(body, action)

        return self._parse_status_response(response, GetStatusZipResponse)

    def _send_soap_request(self, body_content: str, action: str) -> str:
        """Enviar solicitud SOAP con WS-Security."""
        soap_msg = self._build_wssec_soap(body_content, action)

        resp = requests.post(
            self.endpoint,
            data=soap_msg.encode('utf-8'),
            headers={
                'Content-Type': 'application/soap+xml;charset=UTF-8',
                'SOAPAction': action,
            },
            timeout=self.timeout
        )

        return resp.text

    def _build_wssec_soap(self, body_content: str, action: str) -> str:
        """Construir mensaje SOAP con WS-Security firmado."""
        suffix = uuid.uuid4().hex[:8]
        id_ts = f'TS-{suffix}'
        id_tok = f'X509-{suffix}'
        id_sig = f'SIG-{suffix}'
        id_ki = f'KI-{suffix}'
        id_str = f'STR-{suffix}'
        id_to = f'id-TO-{suffix}'

        now = datetime.now(timezone.utc)
        exp = now + timedelta(hours=5)

        created_str = now.strftime('%Y-%m-%dT%H:%M:%S.') + f'{now.microsecond // 1000:03d}Z'
        expires_str = exp.strftime('%Y-%m-%dT%H:%M:%S.') + f'{exp.microsecond // 1000:03d}Z'

        soap_template = f'''<soap:Envelope xmlns:soap="{NS_SOAP['soap']}" xmlns:wcf="{NS_SOAP['wcf']}">
<soap:Header xmlns:wsa="{NS_SOAP['wsa']}">
<wsse:Security xmlns:wsse="{NS_SOAP['wsse']}" xmlns:wsu="{NS_SOAP['wsu']}">
<wsu:Timestamp wsu:Id="{id_ts}">
<wsu:Created>{created_str}</wsu:Created>
<wsu:Expires>{expires_str}</wsu:Expires>
</wsu:Timestamp>
<wsse:BinarySecurityToken EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary" ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3" wsu:Id="{id_tok}">{self.cert_b64}</wsse:BinarySecurityToken>
<ds:Signature xmlns:ds="{NS_SOAP['ds']}" Id="{id_sig}">
<ds:KeyInfo Id="{id_ki}">
<wsse:SecurityTokenReference wsu:Id="{id_str}">
<wsse:Reference URI="#{id_tok}" ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3"/>
</wsse:SecurityTokenReference>
</ds:KeyInfo>
</ds:Signature>
</wsse:Security>
<wsa:Action>{action}</wsa:Action>
<wsa:To xmlns:wsu="{NS_SOAP['wsu']}" wsu:Id="{id_to}">{self.endpoint}</wsa:To>
</soap:Header>
<soap:Body>{body_content}</soap:Body>
</soap:Envelope>'''

        doc = etree.fromstring(soap_template.encode('utf-8'))

        timestamp = doc.find('.//{%s}Timestamp' % NS_SOAP['wsu'])
        to_el = doc.find('.//{%s}To' % NS_SOAP['wsa'])

        ts_c14n = etree.tostring(
            timestamp, method='c14n', exclusive=True, with_comments=False,
            inclusive_ns_prefixes=['wsu', 'soap']
        )
        ts_digest = sha256_digest(ts_c14n)

        to_c14n = etree.tostring(
            to_el, method='c14n', exclusive=True, with_comments=False,
            inclusive_ns_prefixes=['wsu', 'soap', 'wsa']
        )
        to_digest = sha256_digest(to_c14n)

        sig = doc.find('.//{%s}Signature' % NS_SOAP['ds'])

        signed_info_xml = f'''<ds:SignedInfo xmlns:ds="{NS_SOAP['ds']}" xmlns:soap="{NS_SOAP['soap']}" xmlns:wsa="{NS_SOAP['wsa']}" xmlns:wsu="{NS_SOAP['wsu']}">
<ds:CanonicalizationMethod Algorithm="{C14N_EXC_ALG}">
<ec:InclusiveNamespaces xmlns:ec="{NS_SOAP['ec']}" PrefixList="soap wsa"/>
</ds:CanonicalizationMethod>
<ds:SignatureMethod Algorithm="{RSA_SHA256}"/>
<ds:Reference URI="#{id_ts}">
<ds:Transforms>
<ds:Transform Algorithm="{C14N_EXC_ALG}">
<ec:InclusiveNamespaces xmlns:ec="{NS_SOAP['ec']}" PrefixList="wsu soap"/>
</ds:Transform>
</ds:Transforms>
<ds:DigestMethod Algorithm="{SHA256_ALG}"/>
<ds:DigestValue>{ts_digest}</ds:DigestValue>
</ds:Reference>
<ds:Reference URI="#{id_to}">
<ds:Transforms>
<ds:Transform Algorithm="{C14N_EXC_ALG}">
<ec:InclusiveNamespaces xmlns:ec="{NS_SOAP['ec']}" PrefixList="wsu soap wsa"/>
</ds:Transform>
</ds:Transforms>
<ds:DigestMethod Algorithm="{SHA256_ALG}"/>
<ds:DigestValue>{to_digest}</ds:DigestValue>
</ds:Reference>
</ds:SignedInfo>'''

        si_doc = etree.fromstring(signed_info_xml.encode('utf-8'))
        si_c14n = etree.tostring(
            si_doc, method='c14n', exclusive=True, with_comments=False,
            inclusive_ns_prefixes=['soap', 'wsa']
        )

        sig_value = sign_data(self.private_key, si_c14n)

        # Crear SignatureValue
        sig_val_el = etree.Element('{%s}SignatureValue' % NS_SOAP['ds'])
        sig_val_el.text = sig_value

        # Obtener KeyInfo existente
        key_info = sig.find('.//{%s}KeyInfo' % NS_SOAP['ds'])

        # Limpiar Signature y reconstruir con el SignedInfo que firmamos
        sig.remove(key_info)

        # Insertar en orden: SignedInfo, SignatureValue, KeyInfo
        sig.insert(0, si_doc)
        sig.insert(1, sig_val_el)
        sig.append(key_info)

        return etree.tostring(doc, encoding='unicode')

    def _parse_send_test_set_response(self, xml_response: str) -> SendTestSetResponse:
        """Parsear respuesta de SendTestSetAsync/SendBillAsync."""
        response = SendTestSetResponse(xml_response=xml_response)

        try:
            doc = etree.fromstring(xml_response.encode('utf-8'))

            # Buscar ZipKey en diferentes namespaces
            ns_data = 'http://schemas.datacontract.org/2004/07/UploadDocumentResponse'
            ns_dian = 'http://wcf.dian.colombia'

            zip_key = doc.find(f'.//{{{ns_data}}}ZipKey')
            if zip_key is None:
                zip_key = doc.find(f'.//{{{ns_dian}}}ZipKey')

            if zip_key is not None and zip_key.text:
                response.zip_key = zip_key.text

            # Buscar errores
            error_list = doc.findall(f'.//{{{ns_dian}}}string')
            if error_list:
                response.error_messages = [e.text for e in error_list if e.text]

        except Exception:
            pass

        return response

    def _parse_status_response(self, xml_response: str, response_class) -> DianResponse:
        """Parsear respuesta de GetStatusZip/GetStatus."""
        response = response_class(xml_response=xml_response)

        try:
            doc = etree.fromstring(xml_response.encode('utf-8'))

            ns_data = 'http://schemas.datacontract.org/2004/07/DianResponse'
            ns_dian = 'http://wcf.dian.colombia'

            # IsValid
            is_valid = doc.find(f'.//{{{ns_data}}}IsValid')
            if is_valid is None:
                is_valid = doc.find(f'.//{{{ns_dian}}}IsValid')
            if is_valid is not None:
                response.is_valid = is_valid.text.lower() == 'true'

            # StatusCode
            status_code = doc.find(f'.//{{{ns_data}}}StatusCode')
            if status_code is None:
                status_code = doc.find(f'.//{{{ns_dian}}}StatusCode')
            if status_code is not None:
                response.status_code = status_code.text

            # StatusDescription
            status_desc = doc.find(f'.//{{{ns_data}}}StatusDescription')
            if status_desc is None:
                status_desc = doc.find(f'.//{{{ns_dian}}}StatusDescription')
            if status_desc is not None:
                response.status_description = status_desc.text

            # StatusMessage
            status_msgs = doc.findall(f'.//{{{ns_data}}}StatusMessage')
            if not status_msgs:
                status_msgs = doc.findall(f'.//{{{ns_dian}}}StatusMessage')
            if status_msgs:
                msgs = [m.text for m in status_msgs if m.text]
                response.status_message = '; '.join(msgs)

            # ErrorMessage
            error_msgs = doc.findall(f'.//{{{ns_data}}}ErrorMessage')
            if not error_msgs:
                error_msgs = doc.findall(f'.//{{{ns_dian}}}ErrorMessage')
            if error_msgs:
                response.error_messages = [e.text for e in error_msgs if e.text]

        except Exception:
            pass

        return response

    # =========================================================================
    # METODOS DE VERIFICACION Y BATCH
    # =========================================================================

    def verify_status_with_retry(
        self,
        zip_key: str,
        wait_seconds: int = 10,
        max_retries: int = 3,
        on_retry: Callable[[int], None] = None
    ) -> GetStatusZipResponse:
        """
        Verificar estado de documento con espera y reintentos.

        Args:
            zip_key: ZipKey del documento
            wait_seconds: Segundos a esperar antes de verificar
            max_retries: Numero maximo de reintentos
            on_retry: Callback opcional llamado en cada reintento

        Returns:
            GetStatusZipResponse con el estado del documento
        """
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        for attempt in range(max_retries):
            try:
                response = self.get_status_zip(zip_key)

                # Si tenemos un estado definitivo, retornar
                if response.is_valid is not None:
                    return response

                # Si no hay estado, esperar y reintentar
                if attempt < max_retries - 1:
                    if on_retry:
                        on_retry(attempt + 1)
                    time.sleep(wait_seconds)

            except requests.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(wait_seconds)
                else:
                    raise

        return response

    def send_and_verify(
        self,
        file_name: str,
        content_file: bytes,
        test_set_id: str = None,
        wait_seconds: int = 10,
        verify: bool = True
    ) -> Dict[str, Any]:
        """
        Enviar documento y verificar estado.

        Args:
            file_name: Nombre del archivo ZIP
            content_file: Contenido del archivo ZIP en bytes
            test_set_id: ID del set de pruebas (si es habilitacion)
            wait_seconds: Segundos a esperar antes de verificar
            verify: Si se debe verificar el estado despues de enviar

        Returns:
            Diccionario con resultado del envio y verificacion
        """
        result = {
            'send_response': None,
            'status_response': None,
            'is_valid': None,
            'zip_key': None,
            'error': None,
        }

        try:
            # Enviar documento
            if test_set_id:
                send_response = self.send_test_set_async(file_name, content_file, test_set_id)
            else:
                send_response = self.send_bill_async(file_name, content_file)

            result['send_response'] = send_response
            result['zip_key'] = send_response.zip_key

            # Verificar estado si se obtuvo ZipKey
            if verify and send_response.zip_key:
                status_response = self.verify_status_with_retry(
                    send_response.zip_key,
                    wait_seconds=wait_seconds
                )
                result['status_response'] = status_response
                result['is_valid'] = status_response.is_valid

        except Exception as e:
            result['error'] = str(e)

        return result

    def send_batch(
        self,
        documents: List[Dict[str, Any]],
        test_set_id: str = None,
        verify: bool = True,
        wait_seconds: int = 10,
        on_document_sent: Callable[[int, Dict], None] = None,
        on_document_verified: Callable[[int, Dict], None] = None
    ) -> List[Dict[str, Any]]:
        """
        Enviar lote de documentos a DIAN.

        Args:
            documents: Lista de diccionarios con 'file_name' y 'content_file'
            test_set_id: ID del set de pruebas (si es habilitacion)
            verify: Si se debe verificar cada documento
            wait_seconds: Segundos a esperar entre verificaciones
            on_document_sent: Callback tras enviar cada documento
            on_document_verified: Callback tras verificar cada documento

        Returns:
            Lista de resultados para cada documento

        Ejemplo:
            documents = [
                {'file_name': 'fv001.zip', 'content_file': bytes1},
                {'file_name': 'fv002.zip', 'content_file': bytes2},
            ]
            results = client.send_batch(documents, test_set_id='...')
        """
        results = []

        for idx, doc in enumerate(documents):
            result = self.send_and_verify(
                file_name=doc['file_name'],
                content_file=doc['content_file'],
                test_set_id=test_set_id,
                wait_seconds=wait_seconds,
                verify=verify
            )

            result['index'] = idx
            result['file_name'] = doc['file_name']
            results.append(result)

            if on_document_sent:
                on_document_sent(idx, result)

            if verify and result.get('status_response') and on_document_verified:
                on_document_verified(idx, result)

        return results

    def verify_pending_batch(
        self,
        zip_keys: List[str],
        wait_seconds: int = 5,
        on_verified: Callable[[str, GetStatusZipResponse], None] = None
    ) -> Dict[str, GetStatusZipResponse]:
        """
        Verificar estado de multiples documentos pendientes.

        Args:
            zip_keys: Lista de ZipKeys a verificar
            wait_seconds: Segundos a esperar entre verificaciones
            on_verified: Callback tras verificar cada documento

        Returns:
            Diccionario con ZipKey -> GetStatusZipResponse
        """
        results = {}

        for zip_key in zip_keys:
            try:
                response = self.get_status_zip(zip_key)
                results[zip_key] = response

                if on_verified:
                    on_verified(zip_key, response)

                if wait_seconds > 0:
                    time.sleep(wait_seconds)

            except Exception:
                results[zip_key] = GetStatusZipResponse(
                    is_valid=None,
                    status_description='Error al consultar estado'
                )

        return results


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def calcular_dv(nit: str) -> int:
    """
    Calcular digito de verificacion DIAN.

    Args:
        nit: Numero de identificacion tributaria

    Returns:
        Digito de verificacion (0-9)
    """
    nit = ''.join(filter(str.isdigit, nit))
    primos = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
    nit = nit.zfill(15)
    suma = sum(int(nit[i]) * primos[i] for i in range(15))
    resto = suma % 11
    return 11 - resto if resto > 1 else resto


def calcular_cufe(
    numero: str,
    fecha_emision: str,
    hora_emision: str,
    subtotal: float,
    iva: float,
    total: float,
    nit_emisor: str,
    nit_adquiriente: str,
    clave_tecnica: str,
    tipo_ambiente: str = '2'
) -> str:
    """
    Calcular CUFE segun especificacion DIAN (version legacy).

    Args:
        numero: Numero de factura
        fecha_emision: Fecha en formato YYYY-MM-DD
        hora_emision: Hora en formato HH:MM:SS-05:00
        subtotal: Valor subtotal
        iva: Valor IVA
        total: Valor total
        nit_emisor: NIT del emisor
        nit_adquiriente: NIT del adquiriente
        clave_tecnica: Clave tecnica DIAN
        tipo_ambiente: '1' produccion, '2' pruebas

    Returns:
        CUFE en formato SHA-384 hexadecimal
    """
    cadena = (
        f"{numero}{fecha_emision}{hora_emision}"
        f"{subtotal:.2f}01{iva:.2f}04{0:.2f}03{0:.2f}"
        f"{total:.2f}{nit_emisor}{nit_adquiriente}"
        f"{clave_tecnica}{tipo_ambiente}"
    )
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def calcular_cufe_flexible(
    numero: str,
    fecha_emision: str,
    hora_emision: str,
    subtotal: float,
    impuestos: Dict[str, float],
    total: float,
    nit_emisor: str,
    nit_adquiriente: str,
    clave_tecnica: str,
    tipo_ambiente: str = '2'
) -> str:
    """
    Calcular CUFE con soporte para multiples impuestos.

    Cadena CUFE segun Anexo Tecnico DIAN:
    NumDoc + FecDoc + HoraDoc + ValorBruto + 01 + ValorIVA + 04 + ValorINC +
    03 + ValorICA + ValorTotal + NitEmisor + NumAdquiriente +
    ClaveTecnica + TipoAmbiente

    Args:
        numero: Numero de factura
        fecha_emision: Fecha en formato YYYY-MM-DD
        hora_emision: Hora en formato HH:MM:SS-05:00
        subtotal: Valor subtotal
        impuestos: Diccionario con codigo de impuesto -> monto
                   Ej: {'01': 19000.0, '03': 966.0, '04': 0.0}
        total: Valor total
        nit_emisor: NIT del emisor
        nit_adquiriente: NIT del adquiriente
        clave_tecnica: Clave tecnica DIAN
        tipo_ambiente: '1' produccion, '2' pruebas

    Returns:
        CUFE en formato SHA-384 hexadecimal
    """
    # Obtener valores de impuestos (0 si no existe)
    iva = impuestos.get('01', 0.0)  # IVA
    inc = impuestos.get('04', 0.0)  # INC
    ica = impuestos.get('03', 0.0)  # ICA

    cadena = (
        f"{numero}{fecha_emision}{hora_emision}"
        f"{subtotal:.2f}01{iva:.2f}04{inc:.2f}03{ica:.2f}"
        f"{total:.2f}{nit_emisor}{nit_adquiriente}"
        f"{clave_tecnica}{tipo_ambiente}"
    )
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def calcular_software_security_code(
    software_id: str,
    pin: str,
    numero_factura: str
) -> str:
    """
    Calcular SoftwareSecurityCode.

    SHA384(SoftwareID + PIN + NumeroFactura)

    Args:
        software_id: ID del software DIAN
        pin: PIN del software
        numero_factura: Numero de la factura

    Returns:
        Hash SHA-384 hexadecimal
    """
    cadena = f"{software_id}{pin}{numero_factura}"
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def calcular_cude(
    numero: str,
    fecha_emision: str,
    hora_emision: str,
    subtotal: float,
    iva: float,
    total: float,
    nit_emisor: str,
    nit_adquiriente: str,
    software_pin: str,
    tipo_ambiente: str = '2'
) -> str:
    """
    Calcular CUDE segun especificacion DIAN (version legacy).

    El CUDE (Codigo Unico de Documento Electronico) se usa para
    notas credito y notas debito.

    Args:
        numero: Numero del documento
        fecha_emision: Fecha en formato YYYY-MM-DD
        hora_emision: Hora en formato HH:MM:SS-05:00
        subtotal: Valor subtotal
        iva: Valor IVA
        total: Valor total
        nit_emisor: NIT del emisor
        nit_adquiriente: NIT del adquiriente
        software_pin: PIN del software DIAN
        tipo_ambiente: '1' produccion, '2' pruebas

    Returns:
        CUDE en formato SHA-384 hexadecimal
    """
    # CUDE = SHA384(NumDoc + FecDoc + HoraDoc + ValorBruto + 01 + ValorIVA +
    #               04 + 0 + 03 + 0 + ValorTotal + NitEmisor + NumAdquiriente +
    #               SoftwarePIN + TipoAmbiente)
    cadena = (
        f"{numero}{fecha_emision}{hora_emision}"
        f"{subtotal:.2f}01{iva:.2f}04{0:.2f}03{0:.2f}"
        f"{total:.2f}{nit_emisor}{nit_adquiriente}"
        f"{software_pin}{tipo_ambiente}"
    )
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()


def calcular_cude_flexible(
    numero: str,
    fecha_emision: str,
    hora_emision: str,
    subtotal: float,
    impuestos: Dict[str, float],
    total: float,
    nit_emisor: str,
    nit_adquiriente: str,
    software_pin: str,
    tipo_ambiente: str = '2'
) -> str:
    """
    Calcular CUDE con soporte para multiples impuestos.

    El CUDE (Codigo Unico de Documento Electronico) se usa para
    notas credito, notas debito y documentos soporte.

    Cadena CUDE segun Anexo Tecnico DIAN:
    NumDoc + FecDoc + HoraDoc + ValorBruto + 01 + ValorIVA + 04 + ValorINC +
    03 + ValorICA + ValorTotal + NitEmisor + NumAdquiriente +
    SoftwarePIN + TipoAmbiente

    Args:
        numero: Numero del documento
        fecha_emision: Fecha en formato YYYY-MM-DD
        hora_emision: Hora en formato HH:MM:SS-05:00
        subtotal: Valor subtotal
        impuestos: Diccionario con codigo de impuesto -> monto
                   Ej: {'01': 19000.0, '03': 966.0, '04': 0.0}
        total: Valor total
        nit_emisor: NIT del emisor
        nit_adquiriente: NIT del adquiriente
        software_pin: PIN del software DIAN
        tipo_ambiente: '1' produccion, '2' pruebas

    Returns:
        CUDE en formato SHA-384 hexadecimal
    """
    # Obtener valores de impuestos (0 si no existe)
    iva = impuestos.get('01', 0.0)  # IVA
    inc = impuestos.get('04', 0.0)  # INC
    ica = impuestos.get('03', 0.0)  # ICA

    cadena = (
        f"{numero}{fecha_emision}{hora_emision}"
        f"{subtotal:.2f}01{iva:.2f}04{inc:.2f}03{ica:.2f}"
        f"{total:.2f}{nit_emisor}{nit_adquiriente}"
        f"{software_pin}{tipo_ambiente}"
    )
    return hashlib.sha384(cadena.encode('utf-8')).hexdigest()
