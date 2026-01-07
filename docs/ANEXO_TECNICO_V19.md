# Anexo Tecnico Factura Electronica DIAN v1.9

**Resolucion 000165 (01/NOV/2023)**
**753 paginas - Version 1.9**

Este documento describe la especificacion tecnica para la generacion, transmision, validacion, expedicion y recepcion del sistema de facturacion electronica en Colombia usando el estandar **UBL 2.1** (Universal Business Language).

---

## Tabla de Contenidos

- [1. Informacion General](#1-informacion-general)
- [2. Estructura Factura Electronica](#2-estructura-factura-electronica)
- [3. Generacion del CUFE](#3-generacion-del-cufe)
- [4. Firma Digital XAdES-EPES](#4-firma-digital-xades-epes)
- [5. Web Services DIAN](#5-web-services-dian)
- [6. Reglas de Validacion](#6-reglas-de-validacion)
- [7. Notas Credito y Debito](#7-notas-credito-y-debito)
- [8. ApplicationResponse (Eventos)](#8-applicationresponse-eventos)
- [9. SoftwareSecurityCode](#9-softwaresecuritycode)
- [10. Estado de Implementacion en Facho](#10-estado-de-implementacion-en-facho)

---

## 1. Informacion General

### 1.1 Documentos Electronicos Soportados

| Documento | Tipo UBL | Uso |
|-----------|----------|-----|
| Factura Electronica | Invoice | Factura de venta |
| Nota Credito | CreditNote | Anulacion, devolucion, rebaja |
| Nota Debito | DebitNote | Intereses, otros cargos |
| Evento | ApplicationResponse | Acuse, aceptacion, rechazo, eventos RADIAN |
| Contenedor | AttachedDocument | Envio multiples documentos |

### 1.2 Cambios en Version 1.9

**Reglas nuevas:**
- FAJ43a, FAJ43b: Validacion nombre emisor/adquiriente vs RUT
- FAJ44a, FAJ44b: Validacion NIT emisor/adquiriente vs RUT
- CAD02a, FAD09e, CAD09e, DAD09e, FAN03, AAD09e, CBF03a

**Nuevos tributos:** ICL, INPP, IBUA, ICUI, ADV (codigos 32-36)

**Nuevos Web Services:** GetStatusEvent, GetReferenceNotes

**Nuevo codigo documento:** 48 (PPT - Permiso Proteccion Temporal)

---

## 2. Estructura Factura Electronica

### 2.1 Namespaces Requeridos

```xml
xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
xmlns:sts="http://www.dian.gov.co/contratos/facturaelectronica/v1/Structures"
xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
xmlns:xades="http://uri.etsi.org/01903/v1.3.2#"
```

### 2.2 Extensiones UBL (DianExtensions)

```
XPath: /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sts:DianExtensions
```

| Elemento | Descripcion | Obligatorio |
|----------|-------------|-------------|
| InvoiceControl | Control de autorizacion DIAN | Si |
| InvoiceAuthorization | Numero resolucion autorizacion | Si |
| AuthorizationPeriod | StartDate, EndDate del rango | Si |
| AuthorizedInvoices | Prefix, From, To | Si |
| InvoiceSource | IdentificationCode="CO" | Si |
| SoftwareProvider | ProviderID, SoftwareID, SoftwareSecurityCode | Si |
| AuthorizationProvider | AuthorizationProviderID="800197268" | Si |
| QRCode | URL con CUFE para verificacion | Si |

### 2.3 Campos Principales del Invoice

| Campo | XPath | Descripcion |
|-------|-------|-------------|
| UBLVersionID | /Invoice/cbc:UBLVersionID | Literal "UBL 2.1" |
| CustomizationID | /Invoice/cbc:CustomizationID | Tipo operacion (10, 20, etc.) |
| ProfileID | /Invoice/cbc:ProfileID | "DIAN 2.1: Factura Electronica de Venta" |
| ProfileExecutionID | /Invoice/cbc:ProfileExecutionID | 1=produccion, 2=pruebas |
| ID | /Invoice/cbc:ID | Prefijo + consecutivo |
| UUID | /Invoice/cbc:UUID | CUFE (96 caracteres) |
| IssueDate | /Invoice/cbc:IssueDate | Fecha emision YYYY-MM-DD |
| IssueTime | /Invoice/cbc:IssueTime | Hora HH:MM:SS-05:00 |
| InvoiceTypeCode | /Invoice/cbc:InvoiceTypeCode | 01=venta, 02=exportacion, etc. |
| DocumentCurrencyCode | /Invoice/cbc:DocumentCurrencyCode | "COP" |
| LineCountNumeric | /Invoice/cbc:LineCountNumeric | Cantidad lineas |

### 2.4 Atributos del UUID

```xml
<cbc:UUID schemeID="1" schemeName="CUFE-SHA384">96_caracteres_hexadecimales</cbc:UUID>
```
- **schemeID**: "1" (produccion) o "2" (pruebas)
- **schemeName**: "CUFE-SHA384"

### 2.5 Tipos de Documento (@schemeName para identificacion)

| Codigo | Tipo |
|--------|------|
| 11 | Registro civil |
| 12 | Tarjeta de identidad |
| 13 | Cedula ciudadania |
| 21 | Tarjeta de extranjeria |
| 22 | Cedula extranjeria |
| 31 | NIT |
| 41 | Pasaporte |
| 42 | Documento extranjero |
| 47 | PEP |
| 48 | PPT (nuevo v1.9) |
| 50 | NIT de otro pais |
| 91 | NUIP |

### 2.6 Codigos de Tributo

| Codigo | Nombre | Descripcion |
|--------|--------|-------------|
| 01 | IVA | Impuesto al Valor Agregado |
| 02 | IC | Impuesto al Consumo |
| 03 | ICA | Impuesto de Industria y Comercio |
| 04 | INC | Impuesto Nacional al Consumo |
| 05 | ReteIVA | Retencion IVA |
| 06 | ReteFuente | Retencion en la Fuente |
| 07 | ReteICA | Retencion ICA |
| 08 | ReteCREE | Retencion CREE |
| 20 | FtoHorticultura | Cuota de Fomento Hortofruticola |
| 21 | Timbre | Impuesto de Timbre |
| 22 | Bolsas | Impuesto Bolsas Plasticas |
| 23 | INCarbono | Impuesto Nacional Carbono |
| 24 | INCombustibles | Impuesto Combustibles |
| 25 | Sobretasa Combustibles | Sobretasa Combustibles |
| 26 | Sordicom | Aporte Significativo |
| 30 | IC Datos | Impuesto al Consumo de Datos |
| **32** | **ICL** | **Impuesto al Consumo de Licores** |
| **33** | **INPP** | **Impuesto Nacional Productos Plasticos** |
| **34** | **IBUA** | **Impuesto Bebidas Ultraprocesadas Azucaradas** |
| **35** | **ICUI** | **Impuesto Comestibles Ultraprocesados** |
| **36** | **ADV** | **Ad Valorem** |
| ZZ | Otro | Otros tributos |

> **Nota:** Los codigos 32-36 son nuevos en la version 1.9

### 2.7 Estructura Address

```xml
<cac:Address>
    <cbc:ID>11001</cbc:ID>                          <!-- Codigo municipio -->
    <cbc:CityName>Bogota</cbc:CityName>             <!-- Nombre ciudad -->
    <cbc:PostalZone>110111</cbc:PostalZone>         <!-- Codigo postal -->
    <cbc:CountrySubentity>Bogota</cbc:CountrySubentity>
    <cbc:CountrySubentityCode>11</cbc:CountrySubentityCode>
    <cac:AddressLine>
        <cbc:Line>Carrera 10 # 20-30</cbc:Line>    <!-- Direccion sin ciudad -->
    </cac:AddressLine>
    <cac:Country>
        <cbc:IdentificationCode>CO</cbc:IdentificationCode>
        <cbc:Name languageID="es">Colombia</cbc:Name>
    </cac:Country>
</cac:Address>
```

### 2.8 TaxTotal (Impuestos)

```xml
<cac:TaxTotal>
    <cbc:TaxAmount currencyID="COP">285000.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
        <cbc:TaxableAmount currencyID="COP">1500000.00</cbc:TaxableAmount>
        <cbc:TaxAmount currencyID="COP">285000.00</cbc:TaxAmount>
        <cac:TaxCategory>
            <cbc:Percent>19.00</cbc:Percent>
            <cac:TaxScheme>
                <cbc:ID>01</cbc:ID>
                <cbc:Name>IVA</cbc:Name>
            </cac:TaxScheme>
        </cac:TaxCategory>
    </cac:TaxSubtotal>
</cac:TaxTotal>
```

### 2.9 LegalMonetaryTotal (Totales)

| Elemento | Formula/Descripcion |
|----------|---------------------|
| LineExtensionAmount | Suma de InvoiceLine/LineExtensionAmount |
| TaxExclusiveAmount | Base gravable total |
| TaxInclusiveAmount | LineExtensionAmount + Suma TaxTotal/TaxAmount |
| AllowanceTotalAmount | Suma descuentos globales |
| ChargeTotalAmount | Suma cargos globales |
| PrepaidAmount | Anticipos |
| PayableRoundingAmount | Ajuste redondeo |
| PayableAmount | Valor total a pagar |

**Formula PayableAmount:**
```
PayableAmount = TaxInclusiveAmount - AllowanceTotalAmount + ChargeTotalAmount - PrepaidAmount
```

---

## 3. Generacion del CUFE

### 3.1 Algoritmo

**SHA-384** (96 caracteres hexadecimales)

### 3.2 Composicion

```
CUFE = SHA384(NumFac + FecFac + HorFac + ValFac + CodImp1 + ValImp1 +
              CodImp2 + ValImp2 + CodImp3 + ValImp3 + ValTot +
              NitOFE + NumAdq + ClTec + TipoAmbie)
```

| Variable | XPath | Formato |
|----------|-------|---------|
| NumFac | /Invoice/cbc:ID | Prefijo + consecutivo |
| FecFac | /Invoice/cbc:IssueDate | YYYY-MM-DD |
| HorFac | /Invoice/cbc:IssueTime | HH:MM:SS-05:00 |
| ValFac | LegalMonetaryTotal/LineExtensionAmount | 0.00 (2 decimales truncados) |
| CodImp1 | Fijo | 01 |
| ValImp1 | TaxTotal donde TaxScheme/ID="01" (IVA) | 0.00 o valor |
| CodImp2 | Fijo | 04 |
| ValImp2 | TaxTotal donde TaxScheme/ID="04" (INC) | 0.00 o valor |
| CodImp3 | Fijo | 03 |
| ValImp3 | TaxTotal donde TaxScheme/ID="03" (ICA) | 0.00 o valor |
| ValTot | LegalMonetaryTotal/PayableAmount | 0.00 |
| NitOFE | AccountingSupplierParty/.../CompanyID | Sin DV |
| NumAdq | AccountingCustomerParty/.../CompanyID | Sin DV |
| ClTec | Clave tecnica del rango | Del catalogo DIAN |
| TipoAmbie | ProfileExecutionID | 1 o 2 |

### 3.3 Formato de Valores Monetarios

- Sin separadores de miles
- Punto decimal
- **2 decimales truncados** (no redondeados)
- Ejemplo: 1234567.895 → "1234567.89"

### 3.4 Ejemplo de Calculo

```
NumFac: 323200000129
FecFac: 2019-01-16
HorFac: 10:53:10-05:00
ValFac: 1500000.00
CodImp1: 01
ValImp1: 285000.00
CodImp2: 04
ValImp2: 0.00
CodImp3: 03
ValImp3: 0.00
ValTot: 1785000.00
NitOFE: 700085371
NumAdq: 800199436
ClTec: 693ff6f2a553c3646a063436fd4dd9ded0311471
TipoAmb: 1

Cadena: 3232000001292019-01-1610:53:10-05:001500000.0001285000.00040.00030.001785000.00700085371800199436693ff6f2a553c3646a063436fd4dd9ded03114711

CUFE: 8bb918b19ba22a694f1da11c643b5e9de39adf60311cf179179e9b33381030bcd4c3c3f156c506ed5908f9276f5bd9b4
```

---

## 4. Firma Digital XAdES-EPES

### 4.1 Ubicacion

```
XPath: /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/ds:Signature
```

### 4.2 Estandar

- XMLDSig enveloped
- XAdES-EPES (ETSI TS 101 903)
- Politica de firma v2: `https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf`

### 4.3 Algoritmos Permitidos

| Operacion | Algoritmo | URI |
|-----------|-----------|-----|
| Canonicalizacion | C14N inclusivo | http://www.w3.org/TR/2001/REC-xml-c14n-20010315 |
| Firma | RSA-SHA256 | http://www.w3.org/2001/04/xmldsig-more#rsa-sha256 |
| Firma | RSA-SHA384 | http://www.w3.org/2001/04/xmldsig-more#rsa-sha384 |
| Firma | RSA-SHA512 | http://www.w3.org/2001/04/xmldsig-more#rsa-sha512 |
| Digest | SHA-256 | http://www.w3.org/2001/04/xmlenc#sha256 |
| Digest | SHA-384 | http://www.w3.org/2001/04/xmldsig-more#sha384 |
| Digest | SHA-512 | http://www.w3.org/2001/04/xmlenc#sha512 |

### 4.4 Estructura SignedInfo

```xml
<ds:SignedInfo>
    <ds:CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
    <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>

    <!-- Referencia 1: Documento completo -->
    <ds:Reference Id="ref0" URI="">
        <ds:Transforms>
            <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
        </ds:Transforms>
        <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
        <ds:DigestValue>hash_base64</ds:DigestValue>
    </ds:Reference>

    <!-- Referencia 2: KeyInfo -->
    <ds:Reference URI="#xmldsig-{UUID}-keyinfo">
        <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
        <ds:DigestValue>hash_base64</ds:DigestValue>
    </ds:Reference>

    <!-- Referencia 3: SignedProperties -->
    <ds:Reference Type="http://uri.etsi.org/01903#SignedProperties"
                  URI="#xmldsig-{UUID}-signedprops">
        <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
        <ds:DigestValue>hash_base64</ds:DigestValue>
    </ds:Reference>
</ds:SignedInfo>
```

### 4.5 Secuencia de Firma

1. Crear XML completo **sin** elemento Signature
2. Calcular DigestValue del documento (transform enveloped-signature)
3. Crear KeyInfo con certificado X.509
4. **Inyectar namespaces heredados** a KeyInfo y calcular DigestValue
5. Crear SignedProperties (SigningTime, SigningCertificate, SignaturePolicyIdentifier)
6. **Inyectar namespaces heredados** a SignedProperties y calcular DigestValue
7. Construir SignedInfo con las 3 referencias
8. Firmar SignedInfo canonicalizado → SignatureValue
9. Ensamblar Signature completo
10. Insertar en UBLExtension
11. **NO modificar XML despues de firmar**

### 4.6 SignedProperties

```xml
<xades:SignedProperties Id="xmldsig-{UUID}-signedprops">
    <xades:SignedSignatureProperties>
        <xades:SigningTime>2024-01-15T10:30:00-05:00</xades:SigningTime>

        <xades:SigningCertificate>
            <xades:Cert>
                <xades:CertDigest>
                    <ds:DigestMethod Algorithm="..."/>
                    <ds:DigestValue>hash_certificado</ds:DigestValue>
                </xades:CertDigest>
                <xades:IssuerSerial>
                    <ds:X509IssuerName>CN=...,O=...,C=CO</ds:X509IssuerName>
                    <ds:X509SerialNumber>123456789</ds:X509SerialNumber>
                </xades:IssuerSerial>
            </xades:Cert>
        </xades:SigningCertificate>

        <xades:SignaturePolicyIdentifier>
            <xades:SignaturePolicyId>
                <xades:SigPolicyId>
                    <xades:Identifier>https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf</xades:Identifier>
                </xades:SigPolicyId>
                <xades:SigPolicyHash>
                    <ds:DigestMethod Algorithm="..."/>
                    <ds:DigestValue>hash_politica</ds:DigestValue>
                </xades:SigPolicyHash>
            </xades:SignaturePolicyId>
        </xades:SignaturePolicyIdentifier>

        <xades:SignerRole>
            <xades:ClaimedRoles>
                <xades:ClaimedRole>supplier</xades:ClaimedRole>
            </xades:ClaimedRoles>
        </xades:SignerRole>
    </xades:SignedSignatureProperties>
</xades:SignedProperties>
```

### 4.7 KeyInfo

```xml
<ds:KeyInfo Id="xmldsig-{UUID}-keyinfo">
    <ds:X509Data>
        <ds:X509Certificate>certificado_base64</ds:X509Certificate>
    </ds:X509Data>
</ds:KeyInfo>
```

---

## 5. Web Services DIAN

### 5.1 Aspectos Tecnicos

- Protocolo: **SOAP 1.2**
- Seguridad: **TLS 1.2** con autenticacion mutua
- Estandar: WS-Security 1.0 OASIS, X.509 Certificate Token Profile 1.1
- Zona horaria: UTC-05:00 (Colombia)

### 5.2 Servicios Sincronos

| Servicio | Funcion |
|----------|---------|
| SendBillSync | Envio individual DE |
| SendEventUpdateStatus | Envio eventos |
| GetStatus | Consulta estado por CUFE |
| GetStatusZip | Consulta estado lote por trackId |
| GetNumberingRange | Consulta rangos numeracion |
| GetXmlByDocumentKey | Descarga XML por CUFE |
| **GetStatusEvent** | Consulta eventos asociados (nuevo v1.9) |
| **GetReferenceNotes** | Consulta notas asociadas (nuevo v1.9) |

### 5.3 Servicios Asincronos

| Servicio | Funcion | Limites |
|----------|---------|---------|
| SendBillAsync | Envio lote DE | Max 50 docs, 50 MB |
| SendTestSetAsync | Envio habilitacion | Requiere testSetId |

### 5.4 Nomenclatura Archivos

**XML individual:**
```
{tipo}{nit}{ppp}{aa}{dddddddd}.xml
```
- tipo: fv (factura), nc (nota credito), nd (nota debito), ar (evento), ad (contenedor)
- nit: 10 digitos (ceros a la izquierda)
- ppp: 000 (propio), 001 (gratuita DIAN)
- aa: ultimos 2 digitos ano
- dddddddd: consecutivo hexadecimal

Ejemplo: `fv08001972680001900000011.xml`

**ZIP lote:**
```
z{nit}{ppp}{aa}{dddddddd}.zip
```

### 5.5 URLs DIAN

| Ambiente | URL |
|----------|-----|
| Portal | https://www.dian.gov.co |
| Facturacion | https://facturacion.dian.gov.co |
| Habilitacion | https://catalogo-vpfe-hab.dian.gov.co |
| Produccion | https://vpfe.dian.gov.co |

---

## 6. Reglas de Validacion

### 6.1 Reglas Nuevas en v1.9

| Regla | Descripcion | Severidad |
|-------|-------------|-----------|
| FAJ43a | Validar nombre emisor coincida con RUT | Notificacion |
| FAJ43b | Validar nombre adquiriente coincida con RUT | Notificacion |
| FAJ44a | Validar NIT emisor coincida con RUT | Rechazo |
| FAJ44b | Validar NIT adquiriente coincida con RUT | Rechazo |
| FAD09e | Fecha elaboracion factura = Fecha envio | Rechazo |
| CAD09e | Fecha elaboracion NC = Fecha envio | Rechazo |
| DAD09e | Fecha elaboracion ND = Fecha envio | Rechazo |
| AAD09e | Fecha elaboracion evento = Fecha envio | Rechazo |
| CAD02a | CustomizationID NC valido | Rechazo |
| FAN03 | Validacion nota asociada | Rechazo |
| CBF03a | Validacion referencia factura | Rechazo |

### 6.2 Error ZE02 - Firma Invalida

**Causas principales:**
1. Modificar XML despues de firmar
2. Usar C14N exclusivo (debe ser inclusivo)
3. No inyectar namespaces heredados en KeyInfo/SignedProperties

**Solucion:**
- Usar C14N inclusivo: `http://www.w3.org/TR/2001/REC-xml-c14n-20010315`
- Inyectar namespaces UBL al calcular digests
- No formatear/pretty-print el XML despues de firmar

### 6.3 Error FAJ43b - Nombre no coincide con RUT

**Campo:** `cac:PartyTaxScheme/cbc:RegistrationName`

**Reglas de coincidencia:**

| Aspecto | Comportamiento |
|---------|----------------|
| Mayusculas/minusculas | NO sensible |
| Acentos y tildes | **SI sensible** |
| Espacios multiples | **SI sensible** |
| Caracteres especiales (N, &) | Deben coincidir |

**Normalizacion recomendada:**
```python
def normalizar(nombre):
    import unicodedata
    nombre = nombre.upper()
    nombre = unicodedata.normalize('NFC', nombre)  # Preserva acentos
    nombre = ' '.join(nombre.split())  # Un solo espacio
    return nombre.strip()
```

### 6.4 Validaciones de Fechas

- IssueDate dentro de AuthorizationPeriod (StartDate <= IssueDate <= EndDate)
- IssueDate ≈ SigningTime
- IssueTime en zona horaria -05:00
- DueDate >= IssueDate

### 6.5 Validaciones de Numeracion

- ID dentro del rango autorizado (From <= ID <= To)
- Prefix debe coincidir con el autorizado
- Sin espacios ni caracteres adicionales

### 6.6 Validaciones de Impuestos

- TaxTotal/TaxAmount = Suma(TaxSubtotal/TaxAmount)
- Porcentuales: TaxAmount = TaxableAmount × Percent / 100
- Nominales: TaxAmount = PerUnitAmount × BaseUnitMeasure
- Holgura permitida: ±2.00

### 6.7 Metodo de Redondeo

**Round-half-to-even** (NTC 3711):
- 0-4: mantener
- 6-9: incrementar
- 5 + siguiente par: mantener
- 5 + siguiente impar: incrementar

---

## 7. Notas Credito y Debito

### 7.1 Diferencias con Invoice

| Campo | Nota Credito | Nota Debito |
|-------|--------------|-------------|
| Raiz | CreditNote | DebitNote |
| ProfileID | "DIAN 2.1: Nota Credito de..." | "DIAN 2.1: Nota Debito de..." |
| UUID schemeName | CUDE-SHA384 | CUDE-SHA384 |

### 7.2 Elementos Especificos

```xml
<cac:DiscrepancyResponse>
    <cbc:ReferenceID>SETP990000001</cbc:ReferenceID>
    <cbc:ResponseCode>1</cbc:ResponseCode>  <!-- Ver codigos -->
    <cbc:Description>Anulacion de la factura</cbc:Description>
</cac:DiscrepancyResponse>

<cac:BillingReference>
    <cac:InvoiceDocumentReference>
        <cbc:ID>SETP990000001</cbc:ID>
        <cbc:UUID schemeName="CUFE-SHA384">cufe_factura</cbc:UUID>
        <cbc:IssueDate>2024-01-10</cbc:IssueDate>
    </cac:InvoiceDocumentReference>
</cac:BillingReference>
```

### 7.3 Codigos ResponseCode - Nota Credito

| Codigo | Descripcion |
|--------|-------------|
| 1 | Devolucion parcial de bienes y/o no aceptacion parcial del servicio |
| 2 | Anulacion de factura electronica |
| 3 | Rebaja o descuento parcial o total |
| 4 | Ajuste de precio |
| 6 | Descuento comercial por pronto pago |
| 7 | Descuento comercial por volumen de ventas |

> **Nota:** El codigo 5 "Otros" fue **eliminado** en el Anexo v1.9. Los codigos 6 y 7 tienen significados especificos.

### 7.4 Codigos ResponseCode - Nota Debito

| Codigo | Descripcion |
|--------|-------------|
| 1 | Intereses |
| 2 | Gastos por cobrar |
| 3 | Cambio del valor |
| 4 | Otros |

---

## 8. ApplicationResponse (Eventos)

### 8.1 Tipos de Eventos

| Codigo | Evento | Generador |
|--------|--------|-----------|
| 030 | Acuse de recibo FE | Adquiriente |
| 031 | Recibo bien/servicio | Adquiriente |
| 032 | Aceptacion expresa | Adquiriente |
| 033 | Aceptacion tacita | Emisor |
| 034 | Reclamo factura | Adquiriente |
| 035 | Aval | Avalista |
| 036 | Inscripcion titulo valor | Tenedor |
| 037 | Endoso en propiedad | Tenedor |
| 038 | Endoso en garantia | Tenedor |
| 039 | Endoso en procuracion | Tenedor |
| 040 | Cancelacion endoso | Tenedor |
| 041 | Limitacion circulacion | Tenedor |
| 042 | Terminacion limitacion | Tenedor |
| 043 | Mandato | Tenedor |
| 044 | Terminacion mandato | Tenedor |
| 045 | Pago parcial | Tenedor |
| 046 | Pago total | Tenedor |

### 8.2 Requisitos RADIAN

Para registrar factura como titulo valor:
1. Fecha vencimiento (DueDate)
2. Acuse recibo (030)
3. Recibo bien/servicio (031)
4. Aceptacion expresa/tacita o reclamo (032/033/034)

### 8.3 Estructura ApplicationResponse

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApplicationResponse xmlns="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2">
    <cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>1</cbc:CustomizationID>
    <cbc:ProfileID>DIAN 2.1: ApplicationResponse</cbc:ProfileID>
    <cbc:ProfileExecutionID>1</cbc:ProfileExecutionID>
    <cbc:ID>AR00001</cbc:ID>
    <cbc:UUID schemeName="CUDE-SHA384">cude_evento</cbc:UUID>
    <cbc:IssueDate>2024-01-15</cbc:IssueDate>
    <cbc:IssueTime>10:30:00-05:00</cbc:IssueTime>

    <cac:SenderParty>
        <!-- Datos del emisor del evento -->
    </cac:SenderParty>

    <cac:ReceiverParty>
        <!-- Datos del receptor del evento -->
    </cac:ReceiverParty>

    <cac:DocumentResponse>
        <cac:Response>
            <cbc:ResponseCode>030</cbc:ResponseCode>
            <cbc:Description>Acuse de recibo</cbc:Description>
        </cac:Response>
        <cac:DocumentReference>
            <cbc:ID>SETP990000001</cbc:ID>
            <cbc:UUID schemeName="CUFE-SHA384">cufe_factura</cbc:UUID>
        </cac:DocumentReference>
    </cac:DocumentResponse>
</ApplicationResponse>
```

---

## 9. SoftwareSecurityCode

### 9.1 Calculo

```
SoftwareSecurityCode = SHA384(SoftwareID + PIN + NumeroFactura)
```

- **SoftwareID**: Asignado por DIAN (UUID)
- **PIN**: Asignado por DIAN
- **NumeroFactura**: ID del documento (prefijo + consecutivo)
- **Resultado**: 96 caracteres hexadecimales

### 9.2 Ubicacion

```xml
<sts:SoftwareProvider>
    <sts:ProviderID schemeAgencyID="195"
                    schemeAgencyName="CO, DIAN..."
                    schemeID="4"
                    schemeName="31">900123456</sts:ProviderID>
    <sts:SoftwareID schemeAgencyID="195"
                    schemeAgencyName="CO, DIAN...">uuid-software</sts:SoftwareID>
    <sts:SoftwareSecurityCode schemeAgencyID="195"
                              schemeAgencyName="CO, DIAN...">96_caracteres</sts:SoftwareSecurityCode>
</sts:SoftwareProvider>
```

### 9.3 Implementacion en Facho

```python
import hashlib

def calcular_software_security_code(software_id, pin, numero_factura):
    """
    Calcula el SoftwareSecurityCode segun especificacion DIAN.

    Args:
        software_id: UUID del software asignado por DIAN
        pin: PIN asignado por DIAN
        numero_factura: Prefijo + consecutivo del documento

    Returns:
        str: Hash SHA-384 de 96 caracteres hexadecimales
    """
    cadena = f"{software_id}{pin}{numero_factura}"
    return hashlib.sha384(cadena.encode()).hexdigest()
```

---

## 10. Estado de Implementacion en Facho

### 10.1 Implementado

| Caracteristica | Estado | Notas |
|----------------|--------|-------|
| Estructura UBL 2.1 Invoice | OK | Completo |
| Estructura UBL 2.1 CreditNote | OK | Completo |
| Estructura UBL 2.1 DebitNote | OK | Completo |
| Namespaces DIAN | OK | Completo |
| CUFE/CUDE SHA-384 | OK | Completo |
| Extensiones DIAN | OK | InvoiceControl, SoftwareProvider, etc. |
| Firma XAdES-EPES | OK | Politica v2, C14N inclusivo |
| Cliente WS-Security | OK | SOAP 1.2, TLS 1.2 |
| Listas de codigos | OK | Actualizado v1.9 |
| Timezone Colombia | OK | UTC-05:00 |
| Nuevos tributos (32-36) | OK | ICL, INPP, IBUA, ICUI, ADV |
| Conceptos NC actualizados | OK | Sin codigo 5 "Otros" |
| Tipo documento PPT (48) | OK | Agregado |
| Documento Soporte | OK | Tipo 05 |
| NC Documento Soporte | OK | Tipo 95 |
| SoftwareSecurityCode | OK | SHA-384 |

### 10.2 Pendiente de Implementacion

| Caracteristica | Estado | Prioridad |
|----------------|--------|-----------|
| Validacion local FAJ43a/FAJ43b | Pendiente | Alta |
| Validacion local FAJ44a/FAJ44b | Pendiente | Alta |
| GetStatusEvent | Pendiente | Media |
| GetReferenceNotes | Pendiente | Media |
| ApplicationResponse completo | Parcial | Media |
| Eventos RADIAN (035-046) | Pendiente | Media |
| Control cambiario (modos 50/51) | Pendiente | Baja |
| Sector Salud | No implementado | Baja |
| Sector Transporte | No implementado | Baja |
| Sector Fiduciario | No implementado | Baja |

### 10.3 Recomendaciones de Validacion Local

Antes de enviar a DIAN, validar:

1. **RegistrationName** - Coincida exactamente con RUT (sensible a acentos/espacios)
2. **CompanyID** - NIT valido con DV correcto
3. **Fechas** - Fecha elaboracion = Fecha envio
4. **LineCountNumeric** - Numero correcto de lineas
5. **Rango numeracion** - ID dentro del rango autorizado
6. **Tributos** - Codigos correctos segun producto
7. **Totales** - Formulas correctas, holgura ±2.00

---

## Referencias

### Documentacion Oficial

- [Anexo Tecnico v1.9 DIAN (PDF)](https://www.dian.gov.co/impuestos/factura-electronica/Documents/Anexo-Tecnico-Factura-Electronica-de-Venta-vr-1-9.pdf)
- [Caja de Herramientas v1.9](https://www.dian.gov.co/impuestos/factura-electronica/Paginas/Factura-Electronica.aspx)
- [Resolucion 000165 de 2023](https://www.dian.gov.co/)
- [Portal Factura Electronica DIAN](https://www.dian.gov.co/impuestos/factura-electronica/)

### Repositorios de Referencia

- Python: bit4bit/facho
- PHP: Stenfrank/ubl21dian
- C#: miguelhuertas/eFacturacionColombia_V2.Firma

---

## Historial de Cambios

| Version Anexo | Fecha | Cambios Principales |
|---------------|-------|---------------------|
| 1.9 | Nov 2023 | Nuevos tributos 32-36, reglas FAJ43/44, eventos RADIAN, GetStatusEvent, GetReferenceNotes |
| 1.8 | Feb 2021 | Documento Soporte, nomina electronica |
| 1.7 | 2020 | Version base implementada en Facho |

---

*Documento generado a partir del Anexo Tecnico Factura Electronica de Venta v1.9 - DIAN Colombia*
