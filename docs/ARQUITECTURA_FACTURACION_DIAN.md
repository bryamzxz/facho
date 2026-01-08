# Arquitectura de Facturación Electrónica DIAN - facho

## 1. Visión General del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FACTURACIÓN ELECTRÓNICA DIAN                         │
│                           facho Library - Python                             │
│              Facturas • Notas de Crédito • Notas de Débito                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   EMISOR     │     │    facho     │     │    DIAN      │     │  ADQUIRIENTE │
│  (Empresa    │────▶│   Library    │────▶│  Web Service │────▶│  (Cliente)   │
│   Emisora)   │     │              │     │  Validación  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
      │                     │                    │                     │
      │  Datos Documento    │  XML Firmado       │  Validación         │
      │  Certificado        │  SOAP Request      │  Autorización       │
      │  Configuración      │  ZIP Base64        │  CUFE/CUDE          │
      └─────────────────────┴────────────────────┴─────────────────────┘
```

## 2. Tipos de Documentos Electrónicos Soportados

### Resumen de Documentos

| Documento | Elemento Raíz | TypeCode | UUID | CustomizationID |
|-----------|---------------|----------|------|-----------------|
| Factura | `<Invoice>` | 01 | CUFE-SHA384 | 10 |
| Nota Crédito | `<CreditNote>` | 91 | CUDE-SHA384 | 20 |
| Nota Débito | `<DebitNote>` | 92 | CUDE-SHA384 | 30 |

### Factura Electrónica

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           📄 FACTURA ELECTRÓNICA                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Elemento raíz:    <Invoice>                                               │
│ • Namespace:        urn:oasis:names:specification:ubl:schema:xsd:Invoice-2  │
│ • ProfileID:        DIAN 2.1: Factura Electronica de Venta                  │
│ • InvoiceTypeCode:  01 (Venta), 02 (Exportación), 03 (Contingencia)        │
│ • UUID:             CUFE (Código Único de Factura Electrónica)              │
│ • schemeName:       CUFE-SHA384                                             │
│ • CustomizationID:  10 (Estándar)                                          │
│ • Propósito:        Documentar venta de bienes o servicios                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Nota de Crédito

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         📋 NOTA DE CRÉDITO                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Elemento raíz:    <CreditNote>                                            │
│ • Namespace:        urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2│
│ • ProfileID:        DIAN 2.1: Nota Credito de Factura Electronica de Venta  │
│ • CreditNoteTypeCode: 91                                                    │
│ • UUID:             CUDE (Código Único de Documento Electrónico)            │
│ • schemeName:       CUDE-SHA384                                             │
│ • CustomizationID:  20                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ PROPÓSITO:                                                                  │
│ • Devolución de bienes (ResponseCode: 1)                                    │
│ • Anulación de factura (ResponseCode: 2)                                    │
│ • Rebaja o descuento (ResponseCode: 3)                                      │
│ • Ajuste de precio (ResponseCode: 4)                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Nota de Débito

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         📋 NOTA DE DÉBITO                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Elemento raíz:    <DebitNote>                                             │
│ • Namespace:        urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2 │
│ • ProfileID:        DIAN 2.1: Nota Debito de Factura Electronica de Venta   │
│ • DebitNoteTypeCode: 92                                                     │
│ • UUID:             CUDE (Código Único de Documento Electrónico)            │
│ • schemeName:       CUDE-SHA384                                             │
│ • CustomizationID:  30                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ PROPÓSITO:                                                                  │
│ • Intereses por mora (ResponseCode: 1)                                      │
│ • Gastos adicionales (ResponseCode: 2)                                      │
│ • Cambio del valor (ResponseCode: 3)                                        │
│ • Otros cargos (ResponseCode: 4)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. Estructura de Referencias en Notas

Las Notas de Crédito y Débito **DEBEN** referenciar una factura existente:

```
FACTURA ORIGINAL                          NOTA CRÉDITO/DÉBITO
┌─────────────────────┐                   ┌─────────────────────────────────────┐
│ Invoice             │                   │ CreditNote / DebitNote              │
│ ├─ ID: SETP990001   │◄──────────────────┤ ├─ DiscrepancyResponse              │
│ ├─ UUID: abc123...  │    (Referencia)   │ │   ├─ ReferenceID: SETP990001     │
│ └─ IssueDate: ...   │                   │ │   ├─ ResponseCode: 2             │
└─────────────────────┘                   │ │   └─ Description: "..."          │
                                          │ │                                   │
                                          │ └─ BillingReference                 │
                                          │     └─ InvoiceDocumentReference     │
                                          │         ├─ ID: SETP990001          │
                                          │         ├─ UUID: abc123... (CUFE)  │
                                          │         └─ IssueDate: 2026-01-08   │
                                          └─────────────────────────────────────┘
```

**IMPORTANTE**: El orden es `DiscrepancyResponse` ANTES de `BillingReference`.

### XML Ejemplo

```xml
<cac:DiscrepancyResponse>
    <cbc:ReferenceID>SETP990000001</cbc:ReferenceID>
    <cbc:ResponseCode>2</cbc:ResponseCode>
    <cbc:Description>Anulación de factura electrónica</cbc:Description>
</cac:DiscrepancyResponse>

<cac:BillingReference>
    <cac:InvoiceDocumentReference>
        <cbc:ID>SETP990000001</cbc:ID>
        <cbc:UUID schemeName="CUFE-SHA384">abc123...</cbc:UUID>
        <cbc:IssueDate>2026-01-08</cbc:IssueDate>
    </cac:InvoiceDocumentReference>
</cac:BillingReference>
```

## 4. Cálculo de CUFE vs CUDE

### CUFE (Facturas Electrónicas)

```
CUFE = SHA384(
    NumFac +           ← Número de factura (SETP990000001)
    FecFac +           ← Fecha emisión (2026-01-08)
    HorFac +           ← Hora emisión (10:30:00-05:00)
    ValFac +           ← Valor sin impuestos (100000.00)
    "01" + ValIVA +    ← Código IVA + valor IVA (19000.00)
    "04" + ValINC +    ← Código INC + valor INC (0.00)
    "03" + ValICA +    ← Código ICA + valor ICA (0.00)
    ValTotal +         ← Valor total (119000.00)
    NITEmisor +        ← NIT del facturador
    NITAdquiriente +   ← NIT del cliente
    ClaveTécnica +     ← Clave técnica DIAN ⚠️
    TipoAmbiente       ← 1 (producción) o 2 (pruebas)
)
```

### CUDE (Notas Crédito y Débito)

```
CUDE = SHA384(
    NumDoc +           ← Número del documento
    FecDoc +           ← Fecha emisión
    HorDoc +           ← Hora emisión
    ValDoc +           ← Valor sin impuestos
    "01" + ValIVA +    ← Código IVA + valor IVA
    "04" + ValINC +    ← Código INC + valor INC
    "03" + ValICA +    ← Código ICA + valor ICA
    ValTotal +         ← Valor total
    NITEmisor +        ← NIT del facturador
    NITAdquiriente +   ← NIT del cliente
    PIN +              ← PIN del software (NO clave técnica) ⚠️
    TipoAmbiente       ← 1 (producción) o 2 (pruebas)
)
```

**⚠️ DIFERENCIA CLAVE**: CUDE usa `software_pin` en lugar de `clave_técnica`.

### Uso en facho

```python
from facho.fe.client.dian_simple import calcular_cufe, calcular_cude

# Para facturas
cufe = calcular_cufe(
    numero='SETP990000001',
    fecha_emision='2026-01-08',
    hora_emision='10:30:00-05:00',
    subtotal=100000.00,
    iva=19000.00,
    total=119000.00,
    nit_emisor='1001186599',
    nit_adquiriente='222222222',
    clave_tecnica='fc8eac422...',  # Clave técnica
    tipo_ambiente='2'
)

# Para notas crédito/débito
cude = calcular_cude(
    numero='SETP990000031',
    fecha_emision='2026-01-08',
    hora_emision='10:35:00-05:00',
    subtotal=50000.00,
    iva=9500.00,
    total=59500.00,
    nit_emisor='1001186599',
    nit_adquiriente='222222222',
    software_pin='12345',  # PIN del software (diferente!)
    tipo_ambiente='2'
)
```

## 5. Estructura XML por Tipo de Documento

```
FACTURA (Invoice)                 NOTA CRÉDITO               NOTA DÉBITO
─────────────────                 ────────────               ───────────
<Invoice                          <CreditNote                <DebitNote
  xmlns="...Invoice-2">             xmlns="...CreditNote-2">   xmlns="...DebitNote-2">

  <UBLExtensions>                   <UBLExtensions>            <UBLExtensions>
    <DianExtensions>                  <DianExtensions>           <DianExtensions>
      <InvoiceControl>✓               (sin InvoiceControl)       (sin InvoiceControl)
    </DianExtensions>                 </DianExtensions>          </DianExtensions>
    <ds:Signature/>                   <ds:Signature/>            <ds:Signature/>
  </UBLExtensions>                  </UBLExtensions>           </UBLExtensions>

  <CustomizationID>10</>            <CustomizationID>20</>     <CustomizationID>30</>
  <UUID schemeName=                 <UUID schemeName=          <UUID schemeName=
    "CUFE-SHA384"/>                   "CUDE-SHA384"/>            "CUDE-SHA384"/>
  <InvoiceTypeCode>01</>            <CreditNoteTypeCode>91</>  <DebitNoteTypeCode>92</>

  (sin DiscrepancyResponse)         <DiscrepancyResponse>      <DiscrepancyResponse>
                                      <ReferenceID/>             <ReferenceID/>
                                      <ResponseCode/>            <ResponseCode/>
                                    </DiscrepancyResponse>     </DiscrepancyResponse>

  (sin BillingReference)            <BillingReference>         <BillingReference>
                                      <InvoiceDocRef>...</>      <InvoiceDocRef>...</>
                                    </BillingReference>        </BillingReference>

  <LegalMonetaryTotal/>             <LegalMonetaryTotal/>      <RequestedMonetaryTotal/>

  <InvoiceLine>                     <CreditNoteLine>           <DebitNoteLine>
    <InvoicedQuantity/>               <CreditedQuantity/>        <DebitedQuantity/>
  </InvoiceLine>                    </CreditNoteLine>          </DebitNoteLine>

</Invoice>                        </CreditNote>              </DebitNote>
```

## 6. Namespaces Requeridos

### Namespace Raíz (cambia según documento)

| Documento | Namespace |
|-----------|-----------|
| Factura | `urn:oasis:names:specification:ubl:schema:xsd:Invoice-2` |
| Nota Crédito | `urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2` |
| Nota Débito | `urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2` |

### Namespaces Comunes

| Prefijo | Namespace |
|---------|-----------|
| `cac:` | `urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2` |
| `cbc:` | `urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2` |
| `ext:` | `urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2` |
| `sts:` | `dian:gov:co:facturaelectronica:Structures-2-1` |
| `ds:` | `http://www.w3.org/2000/09/xmldsig#` |
| `xades:` | `http://uri.etsi.org/01903/v1.3.2#` |

## 7. Nomenclatura de Archivos ZIP

| Documento | Prefijo | Ejemplo |
|-----------|---------|---------|
| Factura | `fv` | `fvSETP990000001.zip` |
| Nota Crédito | `nc` | `ncSETP990000031.zip` |
| Nota Débito | `nd` | `ndSETP990000041.zip` |

Contenido del ZIP:
```
fvSETP990000001.zip
└── fvSETP990000001.xml  (documento XML firmado)
```

## 8. Firma Digital XAdES-EPES

La firma es **IDÉNTICA** para los tres tipos de documentos.

### Proceso de 5 Pasos

1. **Calcular digest del documento** (antes de insertar firma)
   ```
   doc_c14n → SHA-256 → Base64 → DigestValue[0]
   ```

2. **Insertar estructura de firma** en `UBLExtension[2]`
   ```
   ds:Signature con SignedInfo, KeyInfo, SignedProperties
   ```

3. **Calcular digest de KeyInfo**
   ```
   KeyInfo_c14n → SHA-256 → Base64 → DigestValue[1]
   ```

4. **Calcular digest de SignedProperties**
   ```
   SignedProps_c14n → SHA-256 → Base64 → DigestValue[2]
   ```

5. **Firmar SignedInfo**
   ```
   SignedInfo_c14n → RSA-SHA256(PrivateKey) → Base64 → SignatureValue
   ```

### Claves del Éxito

- Usar **C14N INCLUSIVO** (`exclusive=False`)
- lxml propaga namespaces automáticamente
- NO modificar XML después de firmar
- Política DIAN v2: `https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf`

## 9. Requisitos TestSet DIAN

### Documentos Requeridos para Habilitación

| Tipo | Cantidad | Notas |
|------|----------|-------|
| Facturas | 30 | InvoiceTypeCode: 01 |
| Notas de Crédito | 10 | Requieren factura de referencia |
| Notas de Débito | 10 | Requieren factura de referencia |
| **TOTAL** | **50** | |

### Flujo de Dependencias

```
Enviar 30 Facturas ─────────────────────────────────────┐
      │                                                  │
      ├─ Factura 1 ──┬──▶ Nota Crédito 1               │
      │              └──▶ Nota Débito 1                 │
      │                                                  │
      ├─ Factura 2 ──┬──▶ Nota Crédito 2               │
      │              └──▶ Nota Débito 2                 │
      │                                                  │
      ├─ ...                                            │
      │                                                  │
      └─ Factura 10 ─┬──▶ Nota Crédito 10              │
                     └──▶ Nota Débito 10               │
                                                        │
(Facturas 11-30 no necesitan notas asociadas)          │
```

## 10. Uso con facho

### Crear Factura

```python
from facho.fe.builders import InvoiceBuilder, InvoiceConfig, InvoiceData, Party, InvoiceLine, Address
from facho.fe.signing import XAdESSigner
from facho.fe.client import DianSimpleClient

# Configuración
config = InvoiceConfig(
    software_id="...",
    software_pin="...",
    technical_key="...",
    nit="1001186599",
    company_name="Mi Empresa",
    resolution_number="18760000001",
    resolution_date="2019-01-19",
    resolution_end_date="2030-01-19",
    prefix="SETP",
    range_from="990000000",
    range_to="995000000",
    environment="2"  # Pruebas
)

# Datos de factura
invoice_data = InvoiceData(
    number="SETP990000001",
    issue_date="2026-01-08",
    issue_time="10:30:00-05:00",
    supplier=Party(...),
    customer=Party(...),
    lines=[InvoiceLine(...)]
)

# Construir y firmar
builder = InvoiceBuilder(config)
xml = builder.build(invoice_data)

signer = XAdESSigner.from_pkcs12("certificado.pfx", "password")
xml_signed = signer.sign(xml)
```

### Crear Nota Crédito

```python
from facho.fe.builders import CreditNoteBuilder, CreditNoteData

credit_note_data = CreditNoteData(
    number="SETP990000031",
    issue_date="2026-01-08",
    issue_time="10:35:00-05:00",
    supplier=supplier,
    customer=customer,
    lines=[...],
    # Referencias a factura original
    billing_reference_id="SETP990000001",
    billing_reference_uuid="abc123...",  # CUFE de la factura
    billing_reference_date="2026-01-08",
    discrepancy_response_code="2",  # Anulación
    discrepancy_description="Anulación de factura electrónica"
)

builder = CreditNoteBuilder(config)
xml = builder.build(credit_note_data)
xml_signed = signer.sign(xml)
```

### Crear Nota Débito

```python
from facho.fe.builders import DebitNoteBuilder, DebitNoteData

debit_note_data = DebitNoteData(
    number="SETP990000041",
    issue_date="2026-01-08",
    issue_time="10:40:00-05:00",
    supplier=supplier,
    customer=customer,
    lines=[...],
    # Referencias a factura original
    billing_reference_id="SETP990000001",
    billing_reference_uuid="abc123...",
    billing_reference_date="2026-01-08",
    discrepancy_response_code="1",  # Intereses
    discrepancy_description="Intereses por mora"
)

builder = DebitNoteBuilder(config)
xml = builder.build(debit_note_data)
xml_signed = signer.sign(xml)
```

### Enviar a DIAN

```python
from facho.fe.client import DianSimpleClient
import zipfile
import io

# Crear ZIP
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    xml_str = etree.tostring(xml_signed, encoding='UTF-8', xml_declaration=True)
    zf.writestr('fvSETP990000001.xml', xml_str)
zip_content = zip_buffer.getvalue()

# Enviar
client = DianSimpleClient(
    certificate_path="certificado.pfx",
    certificate_password="password",
    environment="habilitacion"
)

response = client.send_test_set_async(
    file_name="fvSETP990000001.zip",
    content_file=zip_content,
    test_set_id="..."
)

print(f"ZipKey: {response.zip_key}")

# Verificar estado
import time
time.sleep(20)
status = client.get_status_zip(response.zip_key)
print(f"IsValid: {status.is_valid}")
print(f"StatusCode: {status.status_code}")
```

## 11. Códigos de Error Comunes

### Errores Generales

| Código | Descripción | Solución |
|--------|-------------|----------|
| ZE02 | Firma inválida | Usar C14N inclusivo, no modificar XML después de firmar |
| FAJ43b | Nombre no coincide con RUT | Usar nombre EXACTO del RUT |
| FAB07b | Fecha fuera del rango | Verificar StartDate/EndDate de resolución |

### Errores de Notas

| Código | Descripción | Solución |
|--------|-------------|----------|
| NCR01 | CUFE de factura no encontrado | Verificar que la factura existe en DIAN |
| NCR02 | ResponseCode inválido | Usar códigos válidos (1-4) |
| NDR01 | Factura ya anulada | No se puede crear ND sobre factura anulada |

## 12. Módulos de facho

```
facho/fe/
├── builders/
│   ├── __init__.py           # Exports públicos
│   ├── constants.py          # Constantes DIAN, namespaces, códigos
│   ├── invoice_builder.py    # InvoiceBuilder, InvoiceData, Party, etc.
│   ├── credit_note_builder.py # CreditNoteBuilder, CreditNoteData
│   └── debit_note_builder.py # DebitNoteBuilder, DebitNoteData
├── signing/
│   ├── __init__.py           # Exports públicos
│   ├── certificate.py        # Carga de certificados PKCS#12
│   ├── utils.py              # sha256_digest, sign_data
│   └── xades.py              # XAdESSigner, sign_invoice_xades
└── client/
    ├── __init__.py           # Exports públicos
    ├── dian_simple.py        # DianSimpleClient, calcular_cufe, calcular_cude
    └── tracker.py            # DocumentTracker para seguimiento
```
