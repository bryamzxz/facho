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

- `facho.fe.form`: Modelos de datos (Invoice, Party, Amount, etc.)
- `facho.fe.form_xml`: Generadores XML (DIANInvoiceXML, etc.)
- `facho.fe.fe`: Extensiones DIAN (CUFE, firma, etc.)
- `facho.fe.client.dian`: Cliente para servicios web DIAN

### Flujo de Trabajo

1. **Modelar** el documento usando `facho.fe.form`
2. **Configurar extensiones** DIAN usando `facho.fe.fe`
3. **Generar XML** usando `facho.fe.form_xml`
4. **Firmar** el documento
5. **Enviar** a DIAN (opcional)

## Factura de Venta Nacional

### Ejemplo Completo

```python
import facho.fe.form as form
import facho.fe.form_xml as form_xml
import facho.fe.fe as fe
from datetime import datetime

# Configuracion
PRIVATE_KEY_PATH = 'ruta/certificado.p12'
PRIVATE_PASSPHRASE = 'password'
SOFTWARE_ID = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
SOFTWARE_PIN = '12345'
TECHNICAL_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
NIT_EMPRESA = '900123456'
DV_EMPRESA = '7'

# Crear factura de venta nacional
inv = form.NationalSalesInvoice()

# Periodo de facturacion
inv.set_period(datetime.now(), datetime.now())

# Fecha de emision
inv.set_issue(datetime.now())

# Identificador: Prefijo + Consecutivo
inv.set_ident('SETP990003033')

# Tipo de operacion (ver seccion 6.1.5 del Anexo)
# 10 = Estandar
# 09 = AIU
# 11 = Mandatos
inv.set_operation_type('10')

# Configurar proveedor (emisor)
inv.set_supplier(form.Party(
    legal_name='MI EMPRESA SAS',
    name='MI EMPRESA SAS',
    ident=form.PartyIdentification(NIT_EMPRESA, DV_EMPRESA, '31'),  # NIT
    responsability_code=form.Responsability(['O-07', 'O-09', 'O-14', 'O-48']),
    responsability_regime_code='48',  # Responsable de IVA
    organization_code='1',  # Persona Juridica
    email='facturacion@miempresa.com',
    address=form.Address(
        name='Sede Principal',
        street='Calle 123 #45-67',
        city=form.City('05001', 'Medellin'),
        country=form.Country('CO', 'Colombia'),
        countrysubentity=form.CountrySubentity('05', 'Antioquia')
    )
))

# Configurar cliente (adquiriente)
inv.set_customer(form.Party(
    legal_name='CLIENTE EJEMPLO LTDA',
    name='CLIENTE EJEMPLO LTDA',
    ident=form.PartyIdentification('800123456', '1', '31'),  # NIT
    responsability_code=form.Responsability(['O-48']),
    responsability_regime_code='48',
    organization_code='1',
    email='contabilidad@cliente.com',
    address=form.Address(
        name='',
        street='Carrera 10 #20-30',
        city=form.City('11001', 'Bogota'),
        country=form.Country('CO', 'Colombia'),
        countrysubentity=form.CountrySubentity('11', 'Bogota')
    )
))

# Metodo de pago
inv.set_payment_mean(form.PaymentMean(
    id='1',      # 1=Contado, 2=Credito
    code='10',   # Efectivo (ver seccion 3.4.2)
    due_at=datetime.now(),
    payment_id='1'
))

# Agregar lineas de factura
inv.add_invoice_line(form.InvoiceLine(
    quantity=form.Quantity(2, '94'),  # 94 = Unidad
    description='Producto de ejemplo',
    item=form.StandardItem('PROD001', 'Producto de ejemplo'),
    price=form.Price(
        amount=form.Amount(50000.00),
        type_code='01',  # Precio unitario
        type='Precio unitario'
    ),
    tax=form.TaxTotal(
        subtotals=[
            form.TaxSubTotal(
                percent=19.00,
                scheme=form.TaxScheme('01')  # IVA
            )
        ]
    )
))

# Agregar segunda linea
inv.add_invoice_line(form.InvoiceLine(
    quantity=form.Quantity(1, '94'),
    description='Servicio profesional',
    item=form.StandardItem('SERV001', 'Servicio profesional'),
    price=form.Price(
        amount=form.Amount(200000.00),
        type_code='01',
        type='Precio unitario'
    ),
    tax=form.TaxTotal(
        subtotals=[
            form.TaxSubTotal(
                percent=19.00,
                scheme=form.TaxScheme('01')
            )
        ]
    )
))

# Calcular totales
inv.calculate()

# Crear extensiones DIAN
def extensions(invoice):
    # Codigo de seguridad del software
    security_code = fe.DianXMLExtensionSoftwareSecurityCode(
        SOFTWARE_ID,
        SOFTWARE_PIN,
        invoice.invoice_ident
    )

    # Proveedor de autorizacion
    authorization_provider = fe.DianXMLExtensionAuthorizationProvider()

    # CUFE (Codigo Unico de Factura Electronica)
    cufe = fe.DianXMLExtensionCUFE(
        invoice,
        fe.DianXMLExtensionCUFE.AMBIENTE_PRUEBAS,  # o AMBIENTE_PRODUCCION
        TECHNICAL_KEY
    )

    # Proveedor de software
    nit = form.PartyIdentification(NIT_EMPRESA, DV_EMPRESA, '31')
    software_provider = fe.DianXMLExtensionSoftwareProvider(
        nit,
        nit.dv,
        SOFTWARE_ID
    )

    # Autorizacion de numeracion
    inv_authorization = fe.DianXMLExtensionInvoiceAuthorization(
        'numero_autorizacion',
        datetime(2024, 1, 1),   # Fecha inicio
        datetime(2026, 12, 31), # Fecha fin
        'SETP',                  # Prefijo
        990000001,               # Desde
        995000000                # Hasta
    )

    return [security_code, authorization_provider, cufe, software_provider, inv_authorization]

# Generar XML
xml = form_xml.DIANInvoiceXML(inv)
for extension in extensions(inv):
    xml.add_extension(extension)

# Escribir archivo firmado
form_xml.utils.DIANWriteSigned(
    xml,
    'factura_firmada.xml',
    PRIVATE_KEY_PATH,
    PRIVATE_PASSPHRASE,
    True  # Incluir archivo adjunto
)
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
import facho.fe.form as form
import facho.fe.form_xml as form_xml
from datetime import datetime, date

# Referencia a la factura original
billing_ref = form.CreditNoteDocumentReference(
    ident='SETP990003033',           # Numero de factura
    uuid='cufe-de-la-factura-original',
    date=date(2024, 1, 15)           # Fecha de la factura
)

# Crear nota credito
credit_note = form.CreditNote(billing_ref)

# Configurar datos basicos
credit_note.set_period(datetime.now(), datetime.now())
credit_note.set_issue(datetime.now())
credit_note.set_ident('NC0001990001')  # Prefijo NC + consecutivo
credit_note.set_operation_type('1')    # Devolucion parcial de bienes

# ... configurar supplier, customer, lines igual que factura ...

credit_note.calculate()

# Generar XML
xml = form_xml.DIANCreditNoteXML(credit_note)
# ... agregar extensiones y firmar ...
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
import facho.fe.form as form
from datetime import date

# Referencia a la factura original
billing_ref = form.DebitNoteDocumentReference(
    ident='SETP990003033',
    uuid='cufe-de-la-factura-original',
    date=date(2024, 1, 15)
)

# Crear nota debito
debit_note = form.DebitNote(billing_ref)
debit_note.set_ident('ND0001990001')
debit_note.set_operation_type('1')  # Intereses

# ... configurar resto igual que nota credito ...
```

### Conceptos de Nota Debito

| Codigo | Descripcion |
|--------|-------------|
| 1 | Intereses |
| 2 | Gastos por cobrar |
| 3 | Cambio del valor |
| 4 | Otros |

## Documento Soporte

Para adquisiciones a sujetos no obligados a expedir factura:

```python
import facho.fe.form as form
import facho.fe.form_xml as form_xml

# Crear documento soporte
doc = form.SupportDocument()
doc.set_ident('DS0001990001')
doc.set_operation_type('10')  # Estandar

# Configurar proveedor (quien adquiere)
doc.set_supplier(form.Party(
    # ... datos del adquiriente ...
))

# Configurar vendedor (sujeto no obligado)
doc.set_customer(form.Party(
    # ... datos del vendedor ...
))

# Agregar retenciones si aplica
doc.add_withholding_tax_total(form.WithholdingTaxTotal(
    subtotals=[
        form.WithholdingTaxSubTotal(
            percent=2.5,
            scheme=form.TaxScheme('06')  # ReteFuente
        )
    ]
))

doc.add_invoice_line(form.InvoiceLine(
    # ... datos de la linea ...
))

doc.calculate()

# Generar XML
xml = form_xml.DIANSupportDocumentXML(doc)
```

## Extensiones DIAN

Las extensiones DIAN agregan informacion requerida por la DIAN al documento UBL:

### DianXMLExtensionCUFE

Genera el CUFE (Codigo Unico de Factura Electronica) usando SHA-384:

```python
cufe = fe.DianXMLExtensionCUFE(
    invoice,
    fe.DianXMLExtensionCUFE.AMBIENTE_PRODUCCION,
    'clave_tecnica_asignada_por_dian'
)
```

### DianXMLExtensionInvoiceAuthorization

Informacion de autorizacion de numeracion:

```python
auth = fe.DianXMLExtensionInvoiceAuthorization(
    'numero_resolucion',
    datetime(2024, 1, 1),   # Fecha inicio
    datetime(2026, 12, 31), # Fecha fin
    'SETP',                  # Prefijo autorizado
    1,                       # Numero desde
    1000000                  # Numero hasta
)
```

### DianXMLExtensionSoftwareProvider

Identificacion del proveedor de software:

```python
nit = form.PartyIdentification('900123456', '7', '31')
provider = fe.DianXMLExtensionSoftwareProvider(
    nit,
    nit.dv,
    'id_software_asignado_por_dian'
)
```

### DianXMLExtensionSoftwareSecurityCode

Codigo de seguridad del software:

```python
security = fe.DianXMLExtensionSoftwareSecurityCode(
    'id_software',
    'pin_software',
    'SETP990003033'  # Numero de factura
)
```

## Firma Digital

Facho implementa XAdES-EPES con politica de firma DIAN v2:

```python
import facho.fe.form_xml.utils as utils

# Firmar documento
utils.DIANWriteSigned(
    xml,                      # DIANInvoiceXML o similar
    'documento_firmado.xml',  # Ruta de salida
    'certificado.p12',        # Certificado PKCS#12
    'password',               # Contraseña del certificado
    True                      # Incluir attached document
)
```

### Requisitos del Certificado

- Formato PKCS#12 (.p12 o .pfx)
- Emitido por CA reconocida (Certicamara, GSE, etc.)
- Proposito de firma digital

## Envio a DIAN

```python
from facho.fe.client.dian import DianClient, Habilitacion

# Configurar cliente
client = DianClient(
    Habilitacion.HABILITACION,  # o PRODUCCION
    'certificado.p12',
    'password'
)

# Enviar documento
with open('documento_firmado.xml', 'rb') as f:
    xml_content = f.read()

response = client.send(xml_content, 'nombre_archivo.xml')

# Verificar respuesta
if response.is_valid:
    print(f"CUFE: {response.cufe}")
    print(f"Fecha: {response.fecha}")
else:
    for error in response.errors:
        print(f"Error: {error}")
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

Facho incluye validacion contra los codelists oficiales de la DIAN:

```python
import facho.fe.form as form

# Validacion automatica al crear objetos
try:
    # Codigo de ciudad invalido
    city = form.City('99999', 'Ciudad Invalida')
except ValueError as e:
    print(f"Error: {e}")

# Codigo de impuesto invalido
try:
    scheme = form.TaxScheme('99')
except ValueError as e:
    print(f"Error: {e}")

# Tipo de documento invalido
try:
    ident = form.PartyIdentification('123', '', '99')
except ValueError as e:
    print(f"Error: {e}")
```

### Validador de Resolucion

```python
validator = form.DianResolucion0001Validator()

if not validator.validate(invoice):
    for error in validator.errors:
        print(f"Error: {error}")
    raise RuntimeError("Factura invalida")
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
