# Guia de Uso de Facho

**Facho** es una libreria para modelar y generar documentos XML requeridos para la facturacion electronica en Colombia, asi como una herramienta de consola para facilitar la generacion, firmado y envio de documentos segun el SOAP vigente de la DIAN.

Facho esta diseñado para usarse en conjunto con el documento **Anexo Tecnico de Factura Electronica de Venta v1.9**, ya que sigue la terminologia presente en este.

## Tabla de Contenidos

- [Instalacion](#instalacion)
- [Conceptos Basicos](#conceptos-basicos)
- [Factura de Venta Nacional](#factura-de-venta-nacional)
- [Notas Credito](#notas-credito)
- [Notas Debito](#notas-debito)
- [Documento Soporte](#documento-soporte)
- [Extensiones DIAN](#extensiones-dian)
- [Firma Digital](#firma-digital)
- [Envio a DIAN](#envio-a-dian)
- [CLI](#cli)
- [Validacion](#validacion)
- [Errores Comunes](#errores-comunes)

## Instalacion

```bash
# Desde GitHub
pip install git+https://github.com/bit4bit/facho

# Desde codigo fuente
git clone https://github.com/bit4bit/facho
cd facho
pip install -e .
```

## Conceptos Basicos

### Modulos Principales

El proyecto ofrece dos formas de uso:

**Paquete modular `dian_fe` (recomendado):**
- `dian_fe.InvoiceBuilder`: Constructor de facturas XML
- `dian_fe.CreditNoteBuilder`: Constructor de notas credito
- `dian_fe.DebitNoteBuilder`: Constructor de notas debito
- `dian_fe.XAdESSigner`: Firma XAdES-EPES
- `dian_fe.DianClient`: Cliente para servicios web DIAN

**Paquete clasico `facho.fe`:**
- `facho.fe.builders`: Constructores XML UBL 2.1
- `facho.fe.signing`: Firma XAdES-EPES
- `facho.fe.client`: Cliente para servicios web DIAN

### Flujo de Trabajo

1. **Configurar** los datos de la empresa y resolucion
2. **Crear** el documento usando un Builder
3. **Firmar** el documento con XAdESSigner
4. **Enviar** a DIAN (opcional)

## Factura de Venta Nacional

### Ejemplo Completo

```python
from dian_fe import (
    InvoiceBuilder, InvoiceConfig, Party, Address, InvoiceLine,
    XAdESSigner, DianClient
)

# Configuracion de la empresa y resolucion DIAN
config = InvoiceConfig(
    software_id='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    software_pin='12345',
    technical_key='clave_tecnica_asignada_por_dian',
    nit='900123456',
    company_name='MI EMPRESA SAS',
    resolution_number='18760000001',
    resolution_date='2024-01-01',
    resolution_end_date='2026-12-31',
    prefix='SETP',
    range_from='990000001',
    range_to='995000000',
    environment='2'  # 1=Produccion, 2=Habilitacion
)

# Proveedor (emisor)
supplier = Party(
    nit='900123456',
    dv='7',
    name='MI EMPRESA SAS',
    doc_type='31',  # NIT
    tax_scheme='O-48',  # Responsable de IVA
    organization_type='1',  # Persona Juridica
    email='facturacion@miempresa.com',
    address=Address(
        street='Calle 123 #45-67',
        city_code='05001',
        city_name='Medellin',
        department_code='05',
        department_name='Antioquia',
        country_code='CO'
    )
)

# Cliente (adquiriente)
customer = Party(
    nit='800123456',
    dv='1',
    name='CLIENTE EJEMPLO LTDA',
    doc_type='31',  # NIT
    tax_scheme='O-48',
    organization_type='1',
    email='contabilidad@cliente.com',
    address=Address(
        street='Carrera 10 #20-30',
        city_code='11001',
        city_name='Bogota',
        department_code='11',
        department_name='Bogota',
        country_code='CO'
    )
)

# Lineas de factura
lines = [
    InvoiceLine(
        quantity=2,
        unit_code='94',  # Unidad
        description='Producto de ejemplo',
        price=50000.00,
        tax_percent=19.0,
        tax_code='01'  # IVA
    ),
    InvoiceLine(
        quantity=1,
        unit_code='94',
        description='Servicio profesional',
        price=200000.00,
        tax_percent=19.0,
        tax_code='01'
    )
]

# Crear factura XML
builder = InvoiceBuilder(config)
xml = builder.build(
    number='SETP990003033',
    issue_date='2026-01-08',
    issue_time='10:30:00-05:00',
    supplier=supplier,
    customer=customer,
    lines=lines,
    payment_means_code='10',  # Efectivo
    payment_means_id='1'      # Contado
)

# Firmar con XAdES-EPES
signer = XAdESSigner.from_pkcs12('certificado.p12', 'password')
signed_xml = signer.sign(xml)

# Guardar archivo firmado
with open('factura_firmada.xml', 'wb') as f:
    f.write(signed_xml)
```

### Tipos de Identificacion Fiscal

| Codigo | Descripcion |
|--------|-------------|
| 11 | Registro civil |
| 12 | Tarjeta de identidad |
| 13 | Cedula de ciudadania |
| 21 | Tarjeta de extranjeria |
| 22 | Cedula de extranjeria |
| 31 | NIT |
| 41 | Pasaporte |
| 42 | Documento de identificacion extranjero |
| 47 | PEP (Permiso Especial de Permanencia) |
| 48 | PPT (Permiso por Proteccion Temporal) |
| 50 | NIT de otro pais |
| 91 | NUIP |

### Unidades de Medida Comunes

| Codigo | Descripcion |
|--------|-------------|
| 94 | Unidad |
| EA | Cada uno |
| KGM | Kilogramo |
| LTR | Litro |
| MTR | Metro |
| MTK | Metro cuadrado |
| MTQ | Metro cubico |
| HUR | Hora |
| DAY | Dia |
| MON | Mes |

## Notas Credito

```python
from dian_fe import CreditNoteBuilder, InvoiceConfig, Party, Address, InvoiceLine, XAdESSigner

# Usar la misma configuracion de la factura
config = InvoiceConfig(...)

# Crear builder de nota credito
builder = CreditNoteBuilder(config)

# Generar nota credito
xml = builder.build(
    number='NC0001990001',
    issue_date='2026-01-08',
    issue_time='10:30:00-05:00',
    supplier=supplier,
    customer=customer,
    lines=lines,
    # Referencia a la factura original
    billing_reference_number='SETP990003033',
    billing_reference_cufe='cufe-de-la-factura-original',
    billing_reference_date='2024-01-15',
    # Concepto de nota credito
    discrepancy_response_code='1'  # 1=Devolucion parcial de bienes
)

# Firmar
signer = XAdESSigner.from_pkcs12('certificado.p12', 'password')
signed_xml = signer.sign(xml)
```

### Conceptos de Nota Credito (Anexo 1.9)

| Codigo | Descripcion |
|--------|-------------|
| 1 | Devolucion parcial de los bienes y/o no aceptacion parcial del servicio |
| 2 | Anulacion de factura electronica |
| 3 | Rebaja o descuento parcial o total |
| 4 | Ajuste de precio |
| 6 | Descuento comercial por pronto pago |
| 7 | Descuento comercial por volumen de ventas |

**Nota:** El codigo 5 "Otros" fue eliminado en el Anexo Tecnico v1.9.

## Notas Debito

```python
from dian_fe import DebitNoteBuilder, InvoiceConfig, Party, Address, InvoiceLine, XAdESSigner

# Usar la misma configuracion de la factura
config = InvoiceConfig(...)

# Crear builder de nota debito
builder = DebitNoteBuilder(config)

# Generar nota debito
xml = builder.build(
    number='ND0001990001',
    issue_date='2026-01-08',
    issue_time='10:30:00-05:00',
    supplier=supplier,
    customer=customer,
    lines=lines,
    # Referencia a la factura original
    billing_reference_number='SETP990003033',
    billing_reference_cufe='cufe-de-la-factura-original',
    billing_reference_date='2024-01-15',
    # Concepto de nota debito
    discrepancy_response_code='1'  # 1=Intereses
)

# Firmar
signer = XAdESSigner.from_pkcs12('certificado.p12', 'password')
signed_xml = signer.sign(xml)
```

### Conceptos de Nota Debito

| Codigo | Descripcion |
|--------|-------------|
| 1 | Intereses |
| 2 | Gastos por cobrar |
| 3 | Cambio del valor |
| 4 | Otros |

## Documento Soporte

Para adquisiciones a sujetos no obligados a expedir factura, use el InvoiceBuilder
con el tipo de documento apropiado:

```python
from dian_fe import InvoiceBuilder, InvoiceConfig, Party, Address, InvoiceLine, XAdESSigner

# Configuracion para documento soporte
config = InvoiceConfig(
    software_id='...',
    software_pin='...',
    technical_key='...',
    nit='900123456',
    company_name='MI EMPRESA SAS',
    resolution_number='...',
    resolution_date='...',
    resolution_end_date='...',
    prefix='DS',
    range_from='1',
    range_to='1000000',
    environment='2'
)

# El adquiriente es quien emite el documento soporte
supplier = Party(
    nit='900123456',
    dv='7',
    name='MI EMPRESA SAS',
    # ... datos del adquiriente ...
)

# El vendedor es el sujeto no obligado a facturar
customer = Party(
    nit='1234567890',
    dv='',
    name='VENDEDOR PERSONA NATURAL',
    doc_type='13',  # Cedula
    # ... datos del vendedor ...
)

# Lineas con retenciones si aplica
lines = [
    InvoiceLine(
        quantity=1,
        unit_code='94',
        description='Servicio adquirido',
        price=1000000.00,
        tax_percent=0.0,
        withholding_percent=2.5,  # ReteFuente
        withholding_code='06'
    )
]

builder = InvoiceBuilder(config)
xml = builder.build(
    number='DS0001990001',
    issue_date='2026-01-08',
    issue_time='10:30:00-05:00',
    supplier=supplier,
    customer=customer,
    lines=lines,
    document_type='05'  # Documento Soporte
)

signer = XAdESSigner.from_pkcs12('certificado.p12', 'password')
signed_xml = signer.sign(xml)
```

## Extensiones DIAN

El paquete `dian_fe` genera automaticamente todas las extensiones DIAN requeridas
a partir de la configuracion `InvoiceConfig`:

- **CUFE/CUDE**: Codigo unico calculado con SHA-384
- **SoftwareSecurityCode**: Codigo de seguridad del software
- **InvoiceAuthorization**: Datos de la resolucion de numeracion
- **SoftwareProvider**: Identificacion del proveedor de software

```python
from dian_fe import calcular_cufe, calcular_cude, calcular_software_security_code, calcular_dv

# Calcular CUFE manualmente (normalmente lo hace el builder)
cufe = calcular_cufe(
    numero_factura='SETP990003033',
    fecha_factura='2026-01-08',
    hora_factura='10:30:00-05:00',
    valor_factura='300000.00',
    codigo_impuesto_1='01',
    valor_impuesto_1='57000.00',
    codigo_impuesto_2='04',
    valor_impuesto_2='0.00',
    codigo_impuesto_3='03',
    valor_impuesto_3='0.00',
    valor_total='357000.00',
    nit_emisor='900123456',
    nit_adquiriente='800123456',
    clave_tecnica='clave_tecnica_dian',
    ambiente='2'  # 1=Produccion, 2=Habilitacion
)

# Calcular digito de verificacion
dv = calcular_dv('900123456')  # Retorna '7'

# Codigo de seguridad del software
security_code = calcular_software_security_code(
    software_id='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    software_pin='12345',
    numero_factura='SETP990003033'
)
```

## Firma Digital

El paquete `dian_fe` implementa XAdES-EPES con politica de firma DIAN v2:

```python
from dian_fe import XAdESSigner

# Cargar certificado desde archivo PKCS#12
signer = XAdESSigner.from_pkcs12('certificado.p12', 'password')

# Firmar documento XML (bytes o string)
signed_xml = signer.sign(xml_content)

# Guardar documento firmado
with open('documento_firmado.xml', 'wb') as f:
    f.write(signed_xml)
```

### Requisitos del Certificado

- Formato PKCS#12 (.p12 o .pfx)
- Emitido por CA reconocida (Certicamara, GSE, etc.)
- Proposito de firma digital

## Envio a DIAN

```python
from dian_fe import DianClient
import zipfile
import io

# Crear cliente DIAN
client = DianClient.from_pkcs12('certificado.p12', 'password')

# Leer documento firmado
with open('documento_firmado.xml', 'rb') as f:
    xml_content = f.read()

# Crear ZIP con el documento
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('fv001.xml', xml_content)
zip_content = zip_buffer.getvalue()

# Enviar a ambiente de habilitacion (test set)
response = client.send_test_set_async(
    'fv001.zip',
    zip_content,
    test_set_id='id_set_pruebas_dian'
)

# Verificar respuesta
if response.is_valid:
    print(f"ZipKey: {response.zip_key}")
    print(f"Status: {response.status_code}")
else:
    print(f"Error: {response.status_description}")
    for error in response.errors:
        print(f"  - {error}")

# Consultar estado de procesamiento
status = client.get_status(track_id=response.zip_key)
print(f"Estado: {status.status_description}")
```

## CLI

Facho incluye una herramienta de linea de comandos:

```bash
# Ver ayuda
facho --help

# Generar factura desde archivo Python
facho generate factura.py

# Solo firmar un documento
facho sign documento.xml --key cert.p12 --password clave

# Enviar a ambiente de habilitacion
facho send documento.xml --env habilitacion --key cert.p12 --password clave

# Enviar a produccion
facho send documento.xml --env produccion --key cert.p12 --password clave
```

## Validacion

El paquete `dian_fe` incluye constantes con los codigos oficiales de la DIAN:

```python
from dian_fe import DOC_TYPES, TAX_CODES, CREDIT_REASONS, DEBIT_REASONS

# Tipos de documento de identidad
print(DOC_TYPES)
# {'11': 'Registro civil', '13': 'Cedula', '31': 'NIT', ...}

# Codigos de impuesto
print(TAX_CODES)
# {'01': 'IVA', '02': 'IC', '03': 'ICA', '04': 'INC', ...}

# Conceptos de nota credito
print(CREDIT_REASONS)
# {'1': 'Devolucion parcial', '2': 'Anulacion', '3': 'Rebaja', ...}

# Conceptos de nota debito
print(DEBIT_REASONS)
# {'1': 'Intereses', '2': 'Gastos por cobrar', ...}
```

### Validacion de Datos

```python
from dian_fe import calcular_dv

# Validar NIT calculando el digito de verificacion
nit = '900123456'
dv_calculado = calcular_dv(nit)
dv_proporcionado = '7'

if dv_calculado != dv_proporcionado:
    raise ValueError(f"DV incorrecto: esperado {dv_calculado}, recibido {dv_proporcionado}")
```

## Errores Comunes

### ZE02: Firma digital invalida

**Causa:** La canonicalizacion o namespaces no son correctos.

**Solucion:** Verificar que el certificado sea valido y que el XML no se modifique despues de firmar.

### FAJ43b: Nombre no coincide con RUT

**Causa:** El `RegistrationName` no coincide exactamente con el registrado en el RUT.

**Solucion:**
- Verificar acentos y tildes (son sensibles)
- Verificar espacios adicionales
- El nombre debe coincidir exactamente (no sensible a mayusculas)

### FAD05: ID fuera de rango

**Causa:** El numero de factura esta fuera del rango autorizado.

**Solucion:** Verificar que el consecutivo este dentro del rango de la resolucion de numeracion.

### FAD01: UBLVersionID invalido

**Causa:** Version de UBL incorrecta.

**Solucion:** Facho genera automaticamente "UBL 2.1", no modificar este valor.

### FAD16: LineCountNumeric incorrecto

**Causa:** El numero de lineas declarado no coincide con las lineas reales.

**Solucion:** Facho calcula automaticamente este valor con `invoice.calculate()`.

## Recursos Adicionales

- [Anexo Tecnico v1.9 DIAN](https://www.dian.gov.co/impuestos/factura-electronica/Documents/Anexo-Tecnico-Factura-Electronica-de-Venta-vr-1-9.pdf)
- [Caja de Herramientas v1.9](https://www.dian.gov.co/impuestos/factura-electronica/Paginas/Factura-Electronica.aspx)
- [Ejemplos en /examples](./examples/)
- [Documentacion de API](./docs/API.md)
- [Cambios Anexo v1.9](./docs/ANEXO_TECNICO_V19.md)
