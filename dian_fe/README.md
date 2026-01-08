# DIAN Facturacion Electronica

Libreria Python modular para facturacion electronica DIAN Colombia.

## Caracteristicas

- Facturas electronicas de venta (FE)
- Notas credito (NC)
- Notas debito (ND)
- Firma digital XAdES-EPES (politica DIAN v2)
- Cliente DIAN con WS-Security
- Calculo automatico CUFE/CUDE (SHA-384)
- Compatible con Anexo Tecnico v1.9

## Instalacion

```bash
pip install -e .
```

### Dependencias

- lxml
- cryptography
- requests

## Uso Rapido

### Crear Factura

```python
from dian_fe import (
    InvoiceBuilder, InvoiceConfig, Party, Address, InvoiceLine,
    XAdESSigner, DianClient
)
import io
import zipfile
from lxml import etree

# Configuracion
config = InvoiceConfig(
    software_id='uuid-software',
    software_pin='12345',
    technical_key='clave-tecnica-dian',
    nit='1001186599',
    company_name='MI EMPRESA SAS',
    resolution_number='18760000001',
    resolution_date='2019-01-19',
    resolution_end_date='2030-01-19',
    prefix='SETP',
    range_from='990000000',
    range_to='995000000',
    test_set_id='uuid-test-set',
    environment='2'  # '2' = Pruebas, '1' = Produccion
)

# Direccion
address = Address(
    city_code='11001',
    city_name='Bogota',
    postal_zone='110111',
    country_subentity='Bogota D.C.',
    country_subentity_code='11',
    address_line='Calle 100 # 10-20'
)

# Proveedor (emisor)
supplier = Party(
    nit='1001186599',
    name='MI EMPRESA SAS',
    legal_name='MI EMPRESA SAS',
    organization_code='1',  # Persona Juridica
    tax_level_code='O-07;O-09',
    address=address,
    email='facturacion@miempresa.com'
)

# Cliente (adquiriente)
customer = Party(
    nit='222222222',
    name='CLIENTE PRUEBA',
    legal_name='CLIENTE PRUEBA',
    organization_code='2',  # Persona Natural
    tax_level_code='R-99-PN',
    scheme_name='13',  # Cedula
    address=address,
    email='cliente@email.com'
)

# Lineas de factura
lines = [
    InvoiceLine(
        description='Producto de prueba',
        quantity=1.0,
        unit_code='94',
        unit_price=100000.00,
        tax_percent=19.0,
        item_id='PROD001'
    )
]

# Construir factura
builder = InvoiceBuilder(config)
xml = builder.build(
    number='SETP990000001',
    issue_date='2026-01-08',
    issue_time='10:30:00-05:00',
    supplier=supplier,
    customer=customer,
    lines=lines,
    note='Factura electronica de prueba'
)

# Firmar
signer = XAdESSigner.from_pkcs12('certificado.pfx', 'password')
signed_xml = signer.sign(xml)

# Crear ZIP
xml_bytes = etree.tostring(signed_xml, encoding='UTF-8', xml_declaration=True)
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('fvSETP990000001.xml', xml_bytes)
zip_content = zip_buffer.getvalue()

# Enviar a DIAN
client = DianClient.from_pkcs12('certificado.pfx', 'password', environment='habilitacion')
response = client.send_test_set_async('fvSETP990000001.zip', zip_content, config.test_set_id)

print(f"ZipKey: {response.zip_key}")
```

### Verificar Estado

```python
import time

# Esperar procesamiento
time.sleep(15)

# Verificar
status = client.get_status_zip(response.zip_key)
print(f"IsValid: {status.is_valid}")
print(f"StatusCode: {status.status_code}")
print(f"StatusDescription: {status.status_description}")

if status.error_messages:
    print(f"Errores: {status.error_messages}")
```

### Crear Nota Credito

```python
from dian_fe import CreditNoteBuilder

# Builder de nota credito
nc_builder = CreditNoteBuilder(config)

# Construir nota credito
nc_xml = nc_builder.build(
    number='SETP990000031',
    issue_date='2026-01-08',
    issue_time='10:35:00-05:00',
    supplier=supplier,
    customer=customer,
    lines=lines,
    # Referencia a factura original
    billing_reference_id='SETP990000001',
    billing_reference_uuid='abc123...',  # CUFE de la factura
    billing_reference_date='2026-01-08',
    discrepancy_response_code='2',  # 2 = Anulacion
    discrepancy_description='Anulacion de factura electronica'
)

# Firmar y enviar igual que factura
signed_nc = signer.sign(nc_xml)
```

### Crear Nota Debito

```python
from dian_fe import DebitNoteBuilder

# Builder de nota debito
nd_builder = DebitNoteBuilder(config)

# Construir nota debito
nd_xml = nd_builder.build(
    number='SETP990000041',
    issue_date='2026-01-08',
    issue_time='10:40:00-05:00',
    supplier=supplier,
    customer=customer,
    lines=lines,
    # Referencia a factura original
    billing_reference_id='SETP990000001',
    billing_reference_uuid='abc123...',
    billing_reference_date='2026-01-08',
    discrepancy_response_code='1',  # 1 = Intereses
    discrepancy_description='Intereses por mora'
)

# Firmar y enviar igual que factura
signed_nd = signer.sign(nd_xml)
```

## CLI

```bash
# Consultar estado
python -m dian_fe --status <zipkey> --config config.json

# Ver resumen de tracking
python -m dian_fe --verificar

# Ayuda
python -m dian_fe --help
```

## Estructura del Proyecto

```
dian_fe/
├── __init__.py      # Exportaciones publicas
├── config.py        # Configuracion y constantes (~150 lineas)
├── utils.py         # CUFE, CUDE, DV, hashes (~100 lineas)
├── certificate.py   # Carga de certificados PKCS#12 (~120 lineas)
├── xades_signer.py  # Firma XAdES-EPES (~200 lineas)
├── xml_builder.py   # Generacion XML UBL 2.1 (~550 lineas)
├── dian_client.py   # Cliente SOAP DIAN (~300 lineas)
├── tracker.py       # Tracking de documentos (~100 lineas)
├── cli.py           # Linea de comandos (~120 lineas)
└── README.md        # Esta documentacion
```

**Total: ~1650 lineas** (libreria completa y documentada)

## Tipos de Documento

| Tipo | Codigo | CustomizationID | UUID |
|------|--------|-----------------|------|
| Factura | 01 | 10 | CUFE-SHA384 |
| Nota Credito | 91 | 20 | CUDE-SHA384 |
| Nota Debito | 92 | 30 | CUDE-SHA384 |

## Codigos de Motivo

### Nota Credito (ResponseCode)

| Codigo | Descripcion |
|--------|-------------|
| 1 | Devolucion parcial de bienes |
| 2 | Anulacion de factura electronica |
| 3 | Rebaja o descuento |
| 4 | Ajuste de precio |

### Nota Debito (ResponseCode)

| Codigo | Descripcion |
|--------|-------------|
| 1 | Intereses |
| 2 | Gastos por cobrar |
| 3 | Cambio del valor |
| 4 | Otros |

## Requisitos TestSet DIAN

Para habilitacion, se requiere enviar:

- **30 Facturas** (InvoiceTypeCode: 01)
- **10 Notas Credito** (requieren factura de referencia)
- **10 Notas Debito** (requieren factura de referencia)

**Total: 50 documentos**

## Errores Comunes

| Codigo | Descripcion | Solucion |
|--------|-------------|----------|
| ZE02 | Firma invalida | Usar C14N inclusivo, no modificar XML despues de firmar |
| FAJ43b | Nombre no coincide con RUT | Usar nombre EXACTO del RUT |
| FAB07b | Fecha fuera del rango | Verificar StartDate/EndDate de resolucion |

## Compatibilidad

- Python 3.8+
- Anexo Tecnico DIAN v1.9 (Resolucion 000165/2023)

## Licencia

MIT

## Referencias

- [Anexo Tecnico DIAN](https://www.dian.gov.co/impuestos/factura-electronica/Paginas/default.aspx)
- [Politica de Firma DIAN v2](https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf)
