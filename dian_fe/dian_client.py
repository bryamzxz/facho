# This file is part of dian_fe.
"""
Cliente SOAP para servicios web DIAN.
Implementacion WS-Security sin dependencias de zeep.
"""

import uuid
import base64
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

import requests
from lxml import etree

from .config import NS_SOAP, C14N_EXC_ALG, RSA_SHA256, SHA256_ALG, ENDPOINT_HABILITACION, ENDPOINT_PRODUCCION
from .certificate import cert_to_base64, load_certificate, load_certificate_from_bytes
from .utils import sha256_digest


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
    zip_key: Optional[str] = None


# =============================================================================
# CLIENTE DIAN
# =============================================================================

class DianClient:
    """
    Cliente para servicios web DIAN con WS-Security.

    Soporta envio de documentos en ambiente de habilitacion y produccion.
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

    @classmethod
    def from_pkcs12(cls, pfx_path: str, password: str, environment: str = 'habilitacion') -> 'DianClient':
        """Crear cliente desde archivo PKCS#12."""
        return cls(certificate_path=pfx_path, certificate_password=password, environment=environment)

    def send_test_set_async(
        self,
        file_name: str,
        content_file: bytes,
        test_set_id: str
    ) -> DianResponse:
        """
        Enviar documento de prueba a DIAN (SendTestSetAsync).

        Args:
            file_name: Nombre del archivo ZIP
            content_file: Contenido del archivo ZIP en bytes
            test_set_id: ID del set de pruebas DIAN

        Returns:
            DianResponse con el ZipKey si fue exitoso
        """
        content_b64 = base64.b64encode(content_file).decode('utf-8')

        body = f'''<wcf:SendTestSetAsync xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:fileName>{file_name}</wcf:fileName>
<wcf:contentFile>{content_b64}</wcf:contentFile>
<wcf:testSetId>{test_set_id}</wcf:testSetId>
</wcf:SendTestSetAsync>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendTestSetAsync'
        response = self._send_soap_request(body, action)

        return self._parse_response(response)

    def send_bill_sync(self, file_name: str, content_file: bytes) -> DianResponse:
        """
        Enviar documento sincronicamente a DIAN (SendBillSync).

        Args:
            file_name: Nombre del archivo ZIP
            content_file: Contenido del archivo ZIP en bytes

        Returns:
            DianResponse con el resultado
        """
        content_b64 = base64.b64encode(content_file).decode('utf-8')

        body = f'''<wcf:SendBillSync xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:fileName>{file_name}</wcf:fileName>
<wcf:contentFile>{content_b64}</wcf:contentFile>
</wcf:SendBillSync>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendBillSync'
        response = self._send_soap_request(body, action)

        return self._parse_response(response)

    def send_bill_async(self, file_name: str, content_file: bytes) -> DianResponse:
        """
        Enviar documento asincronicamente a DIAN (SendBillAsync).

        Args:
            file_name: Nombre del archivo ZIP
            content_file: Contenido del archivo ZIP en bytes

        Returns:
            DianResponse con el ZipKey si fue exitoso
        """
        content_b64 = base64.b64encode(content_file).decode('utf-8')

        body = f'''<wcf:SendBillAsync xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:fileName>{file_name}</wcf:fileName>
<wcf:contentFile>{content_b64}</wcf:contentFile>
</wcf:SendBillAsync>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendBillAsync'
        response = self._send_soap_request(body, action)

        return self._parse_response(response)

    def get_status_zip(self, track_id: str) -> DianResponse:
        """
        Consultar estado de documento por TrackId/ZipKey (GetStatusZip).

        Args:
            track_id: TrackId o ZipKey del documento

        Returns:
            DianResponse con el estado
        """
        body = f'''<wcf:GetStatusZip xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:trackId>{track_id}</wcf:trackId>
</wcf:GetStatusZip>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/GetStatusZip'
        response = self._send_soap_request(body, action)

        return self._parse_response(response)

    def get_status(self, track_id: str) -> DianResponse:
        """
        Consultar estado de documento por TrackId (GetStatus).

        Args:
            track_id: TrackId del documento (CUFE/CUDE)

        Returns:
            DianResponse con el estado
        """
        body = f'''<wcf:GetStatus xmlns:wcf="{NS_SOAP['wcf']}">
<wcf:trackId>{track_id}</wcf:trackId>
</wcf:GetStatus>'''

        action = 'http://wcf.dian.colombia/IWcfDianCustomerServices/GetStatus'
        response = self._send_soap_request(body, action)

        return self._parse_response(response)

    def _send_soap_request(self, body_content: str, action: str) -> str:
        """Enviar solicitud SOAP con WS-Security."""
        from .certificate import sign_data

        soap_msg = self._build_wssec_soap(body_content, action, sign_data)

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

    def _build_wssec_soap(self, body_content: str, action: str, sign_func: Callable) -> str:
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

        sig_value = sign_func(self.private_key, si_c14n)

        sig_val_el = etree.Element('{%s}SignatureValue' % NS_SOAP['ds'])
        sig_val_el.text = sig_value

        key_info = sig.find('.//{%s}KeyInfo' % NS_SOAP['ds'])
        sig.remove(key_info)

        sig.insert(0, si_doc)
        sig.insert(1, sig_val_el)
        sig.append(key_info)

        return etree.tostring(doc, encoding='unicode')

    def _parse_response(self, xml_response: str) -> DianResponse:
        """Parsear respuesta de DIAN."""
        response = DianResponse(xml_response=xml_response)

        try:
            doc = etree.fromstring(xml_response.encode('utf-8'))

            ns_data = 'http://schemas.datacontract.org/2004/07/UploadDocumentResponse'
            ns_dian = 'http://wcf.dian.colombia'
            ns_resp = 'http://schemas.datacontract.org/2004/07/DianResponse'

            # ZipKey
            zip_key = doc.find(f'.//{{{ns_data}}}ZipKey')
            if zip_key is None:
                zip_key = doc.find(f'.//{{{ns_dian}}}ZipKey')
            if zip_key is not None and zip_key.text:
                response.zip_key = zip_key.text

            # IsValid
            is_valid = doc.find(f'.//{{{ns_resp}}}IsValid')
            if is_valid is None:
                is_valid = doc.find(f'.//{{{ns_dian}}}IsValid')
            if is_valid is not None:
                response.is_valid = is_valid.text.lower() == 'true'

            # StatusCode
            status_code = doc.find(f'.//{{{ns_resp}}}StatusCode')
            if status_code is None:
                status_code = doc.find(f'.//{{{ns_dian}}}StatusCode')
            if status_code is not None:
                response.status_code = status_code.text

            # StatusDescription
            status_desc = doc.find(f'.//{{{ns_resp}}}StatusDescription')
            if status_desc is None:
                status_desc = doc.find(f'.//{{{ns_dian}}}StatusDescription')
            if status_desc is not None:
                response.status_description = status_desc.text

            # StatusMessage
            status_msgs = doc.findall(f'.//{{{ns_resp}}}StatusMessage')
            if not status_msgs:
                status_msgs = doc.findall(f'.//{{{ns_dian}}}StatusMessage')
            if status_msgs:
                msgs = [m.text for m in status_msgs if m.text]
                response.status_message = '; '.join(msgs)

            # ErrorMessage
            error_msgs = doc.findall(f'.//{{{ns_resp}}}ErrorMessage')
            if not error_msgs:
                error_msgs = doc.findall(f'.//{{{ns_dian}}}ErrorMessage')
            if not error_msgs:
                error_msgs = doc.findall(f'.//{{{ns_dian}}}string')
            if error_msgs:
                response.error_messages = [e.text for e in error_msgs if e.text]

        except Exception:
            pass

        return response

    # =========================================================================
    # METODOS DE CONVENIENCIA
    # =========================================================================

    def verify_status_with_retry(
        self,
        zip_key: str,
        wait_seconds: int = 10,
        max_retries: int = 3
    ) -> DianResponse:
        """
        Verificar estado con espera y reintentos.

        Args:
            zip_key: ZipKey del documento
            wait_seconds: Segundos a esperar antes de verificar
            max_retries: Numero maximo de reintentos

        Returns:
            DianResponse con el estado
        """
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        for attempt in range(max_retries):
            try:
                response = self.get_status_zip(zip_key)
                if response.is_valid is not None:
                    return response
                if attempt < max_retries - 1:
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
        wait_seconds: int = 10
    ) -> Dict[str, Any]:
        """
        Enviar documento y verificar estado.

        Args:
            file_name: Nombre del archivo ZIP
            content_file: Contenido del archivo ZIP
            test_set_id: ID del set de pruebas (si es habilitacion)
            wait_seconds: Segundos a esperar antes de verificar

        Returns:
            Diccionario con resultado
        """
        result = {
            'send_response': None,
            'status_response': None,
            'is_valid': None,
            'zip_key': None,
            'error': None,
        }

        try:
            if test_set_id:
                send_response = self.send_test_set_async(file_name, content_file, test_set_id)
            else:
                send_response = self.send_bill_async(file_name, content_file)

            result['send_response'] = send_response
            result['zip_key'] = send_response.zip_key

            if send_response.zip_key:
                status_response = self.verify_status_with_retry(
                    send_response.zip_key,
                    wait_seconds=wait_seconds
                )
                result['status_response'] = status_response
                result['is_valid'] = status_response.is_valid

        except Exception as e:
            result['error'] = str(e)

        return result
