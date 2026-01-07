# Referencia de API - Facho

Esta documentacion describe las clases y funciones principales de la libreria Facho.

## Tabla de Contenidos

- [facho.fe.form](#fachofeform)
- [facho.fe.form_xml](#fachofeform_xml)
- [facho.fe.fe](#fachofefe)
- [facho.fe.client.dian](#fachofeclientdian)
- [facho.facho](#fachofacho)

---

## facho.fe.form

Modelos de datos para documentos electronicos.

### Invoice

Clase base para todos los tipos de documentos.

```python
class Invoice:
    def __init__(self, type_code: str)
```

**Metodos:**

| Metodo | Descripcion |
|--------|-------------|
| `set_period(start, end)` | Establece el periodo de facturacion |
| `set_issue(datetime)` | Establece la fecha de emision |
| `set_ident(ident)` | Establece el identificador (prefijo + consecutivo) |
| `set_operation_type(operation)` | Establece el tipo de operacion |
| `set_supplier(party)` | Establece el proveedor/emisor |
| `set_customer(party)` | Establece el cliente/adquirente |
| `set_payment_mean(payment)` | Establece el metodo de pago |
| `add_invoice_line(line)` | Agrega una linea de factura |
| `add_allowance_charge(charge)` | Agrega cargo/descuento |
| `add_prepaid_payment(paid)` | Agrega pago anticipado |
| `calculate()` | Calcula totales |

### NationalSalesInvoice

Factura de venta nacional (codigo 01).

```python
class NationalSalesInvoice(Invoice):
    def __init__(self)
```

**Ejemplo:**
```python
inv = form.NationalSalesInvoice()
inv.set_ident('SETP990003033')
inv.set_operation_type('10')
```

### CreditNote

Nota credito (codigo 91).

```python
class CreditNote(Invoice):
    def __init__(self, invoice_document_reference: BillingReference)
```

**Ejemplo:**
```python
ref = form.CreditNoteDocumentReference(
    ident='SETP990003033',
    uuid='cufe-original',
    date=date(2024, 1, 15)
)
cn = form.CreditNote(ref)
cn.set_ident('NC0001990001')
cn.set_operation_type('1')  # Devolucion parcial
```

### DebitNote

Nota debito (codigo 92).

```python
class DebitNote(Invoice):
    def __init__(self, invoice_document_reference: BillingReference)
```

### SupportDocument

Documento soporte (codigo 05).

```python
class SupportDocument(Invoice):
    def __init__(self)
```

**Metodos adicionales:**

| Metodo | Descripcion |
|--------|-------------|
| `add_withholding_tax_total(withholding)` | Agrega retencion |

### SupportDocumentCreditNote

Nota credito de documento soporte (codigo 95).

```python
class SupportDocumentCreditNote(Invoice):
    def __init__(self, document_reference: BillingReference)
```

---

### Party

Representa una parte (emisor o adquirente).

```python
@dataclass
class Party:
    name: str
    ident: PartyIdentification
    responsability_code: Responsability
    responsability_regime_code: str
    organization_code: str
    tax_scheme: TaxScheme = TaxScheme('01')
    phone: str = ''
    address: Address = Address('')
    email: str = ''
    legal_name: str = ''
    legal_company_ident: str = ''
    legal_address: str = ''
```

**Ejemplo:**
```python
party = form.Party(
    legal_name='MI EMPRESA SAS',
    name='MI EMPRESA SAS',
    ident=form.PartyIdentification('900123456', '7', '31'),
    responsability_code=form.Responsability(['O-07', 'O-48']),
    responsability_regime_code='48',
    organization_code='1',
    email='contacto@empresa.com',
    address=form.Address(
        name='Sede Principal',
        street='Calle 123 #45-67',
        city=form.City('05001', 'Medellin'),
        country=form.Country('CO', 'Colombia'),
        countrysubentity=form.CountrySubentity('05', 'Antioquia')
    )
)
```

---

### PartyIdentification

Identificacion fiscal de una parte.

```python
@dataclass
class PartyIdentification:
    number: str      # Numero de identificacion
    dv: str          # Digito de verificacion (para NIT)
    type_fiscal: str # Tipo de documento (31=NIT, 13=CC, etc.)
```

---

### Address

Direccion fisica.

```python
@dataclass
class Address:
    name: str
    street: str = ''
    city: City = City('05001')
    country: Country = Country('CO')
    countrysubentity: CountrySubentity = CountrySubentity('05')
```

---

### City

Ciudad (validada contra codelist).

```python
@dataclass
class City:
    code: str  # Codigo DANE del municipio
    name: str = ''  # Se obtiene automaticamente del codelist
```

---

### Country

Pais (validado contra codelist).

```python
@dataclass
class Country:
    code: str  # Codigo ISO (CO, US, etc.)
    name: str = ''
```

---

### CountrySubentity

Departamento (validado contra codelist).

```python
@dataclass
class CountrySubentity:
    code: str  # Codigo DANE del departamento
    name: str = ''
```

---

### Currency

Moneda (validada contra codelist).

```python
@dataclass
class Currency:
    code: str  # Codigo ISO 4217 (COP, USD, EUR, etc.)
```

**Metodos:**

| Metodo | Descripcion |
|--------|-------------|
| `is_cop()` | True si es Peso Colombiano |
| `is_foreign()` | True si es moneda extranjera |
| `name` | Nombre de la moneda |

---

### Amount

Representa un valor monetario.

```python
class Amount:
    def __init__(self, amount: int | float | str, currency: Currency = Currency('COP'))
```

**Metodos:**

| Metodo | Descripcion |
|--------|-------------|
| `float()` | Retorna el valor como float |
| `round(prec)` | Redondea el valor |
| `truncate_as_string(prec)` | Trunca a string |

**Operadores soportados:** `+`, `-`, `*`, `<`, `==`

---

### Quantity

Representa una cantidad con unidad de medida.

```python
class Quantity:
    def __init__(self, val: int | float, code: str)
```

**Ejemplo:**
```python
qty = form.Quantity(10, '94')  # 10 unidades
qty = form.Quantity(5.5, 'KGM')  # 5.5 kilogramos
```

---

### InvoiceLine

Linea de factura.

```python
@dataclass
class InvoiceLine:
    quantity: Quantity
    description: str
    item: Item
    price: Price
    tax: TaxTotal
    allowance_charge: List[AllowanceCharge] = []
```

**Propiedades:**

| Propiedad | Descripcion |
|-----------|-------------|
| `total_amount` | Monto total de la linea |
| `total_tax_inclusive_amount` | Monto con impuestos |
| `total_tax_exclusive_amount` | Monto sin impuestos |
| `tax_amount` | Monto de impuestos |

---

### Item

Clase base para items.

```python
@dataclass
class Item:
    scheme_name: str
    scheme_agency_id: str
    scheme_id: str
    description: str
    id: str
```

### StandardItem

Item estandar (esquema 999).

```python
class StandardItem(Item):
    def __init__(self, id_: str, description: str = '')
```

### UNSPSCItem

Item con codigo UNSPSC.

```python
class UNSPSCItem(Item):
    def __init__(self, id_: str, description: str = '')
```

---

### Price

Precio de un item.

```python
@dataclass
class Price:
    amount: Amount
    type_code: str  # '01' = Precio unitario
    type: str
    quantity: int = 1
```

---

### TaxTotal

Total de impuestos.

```python
@dataclass
class TaxTotal:
    subtotals: List[TaxSubTotal]
    tax_amount: Amount = Amount(0.0)
    taxable_amount: Amount = Amount(0.0)
```

### TaxSubTotal

Subtotal de impuesto.

```python
@dataclass
class TaxSubTotal:
    percent: float
    scheme: TaxScheme = None
    tax_amount: Amount = Amount(0.0)
```

### TaxScheme

Esquema de impuesto.

```python
@dataclass
class TaxScheme:
    code: str = '01'  # 01=IVA, 02=IC, etc.
```

---

### PaymentMean

Metodo de pago.

```python
class PaymentMean:
    DEBIT = '01'
    CREDIT = '02'

    def __init__(self, id: str, code: str, due_at: datetime, payment_id: str)
```

---

### AllowanceCharge

Cargo o descuento.

```python
@dataclass
class AllowanceCharge:
    charge_indicator: bool = True  # True=cargo, False=descuento
    amount: Amount = Amount(0.0)
    reason: AllowanceChargeReason = None
    base_amount: Amount = Amount(0.0)
    multiplier_factor_numeric: Amount = Amount(1.0)
```

### AllowanceChargeAsDiscount

Descuento (charge_indicator=False).

```python
class AllowanceChargeAsDiscount(AllowanceCharge):
    def __init__(self, amount: Amount = Amount(0.0))
```

---

### Responsability

Responsabilidades fiscales.

```python
@dataclass
class Responsability:
    codes: list  # Lista de codigos de responsabilidad
```

**Ejemplo:**
```python
resp = form.Responsability(['O-07', 'O-09', 'O-48'])
```

---

### BillingReference

Referencia a documento.

```python
@dataclass
class BillingReference:
    ident: str   # Numero del documento
    uuid: str    # CUFE/CUDE del documento
    date: date   # Fecha del documento
```

### CreditNoteDocumentReference

Referencia para notas credito.

### DebitNoteDocumentReference

Referencia para notas debito.

### InvoiceDocumentReference

Referencia para facturas.

---

### WithholdingTaxTotal

Total de retenciones (para documentos soporte).

```python
@dataclass
class WithholdingTaxTotal:
    subtotals: List[WithholdingTaxSubTotal]
    tax_amount: Amount = Amount(0.0)
```

### WithholdingTaxSubTotal

Subtotal de retencion.

```python
@dataclass
class WithholdingTaxSubTotal:
    percent: float
    scheme: TaxScheme = None
    tax_amount: Amount = Amount(0.0)
    taxable_amount: Amount = Amount(0.0)
```

---

## facho.fe.form_xml

Generadores de XML para documentos DIAN.

### DIANInvoiceXML

Genera XML de factura.

```python
class DIANInvoiceXML:
    def __init__(self, invoice: Invoice)
    def add_extension(self, extension)
    def tostring() -> bytes
```

### DIANCreditNoteXML

Genera XML de nota credito.

### DIANDebitNoteXML

Genera XML de nota debito.

### DIANSupportDocumentXML

Genera XML de documento soporte.

### DIANSupportDocumentCreditNoteXML

Genera XML de nota credito de documento soporte.

---

### utils

Utilidades para XML.

```python
# Escribir documento firmado
utils.DIANWriteSigned(
    xml,                  # DIANInvoiceXML o similar
    filepath,             # Ruta de salida
    pkcs12_path,          # Ruta al certificado .p12
    passphrase,           # Contraseña del certificado
    include_attached=True # Incluir attached document
)
```

---

## facho.fe.fe

Extensiones DIAN y firma digital.

### DianXMLExtensionCUFE

Genera CUFE/CUDE.

```python
class DianXMLExtensionCUFE:
    AMBIENTE_PRUEBAS = 2
    AMBIENTE_PRODUCCION = 1

    def __init__(self, invoice, ambiente, clave_tecnica)
```

### DianXMLExtensionInvoiceAuthorization

Autorizacion de numeracion.

```python
class DianXMLExtensionInvoiceAuthorization:
    def __init__(self,
        authorization_number,
        start_date,
        end_date,
        prefix,
        from_number,
        to_number
    )
```

### DianXMLExtensionSoftwareProvider

Proveedor de software.

```python
class DianXMLExtensionSoftwareProvider:
    def __init__(self, nit, dv, software_id)
```

### DianXMLExtensionSoftwareSecurityCode

Codigo de seguridad.

```python
class DianXMLExtensionSoftwareSecurityCode:
    def __init__(self, software_id, pin, invoice_number)
```

### DianXMLExtensionAuthorizationProvider

Proveedor de autorizacion.

```python
class DianXMLExtensionAuthorizationProvider:
    def __init__(self)
```

### DianXMLExtensionSigner

Firma XAdES-EPES.

```python
class DianXMLExtensionSigner:
    def __init__(self, pkcs12_path, passphrase)
```

---

## facho.fe.client.dian

Cliente para servicios web DIAN.

### DianClient

```python
class DianClient:
    def __init__(self, ambiente, pkcs12_path, passphrase)
```

**Metodos:**

| Metodo | Descripcion |
|--------|-------------|
| `send(xml_content, filename)` | Envia documento a DIAN |
| `get_status(track_id)` | Consulta estado de documento |

### Habilitacion

Ambientes disponibles.

```python
class Habilitacion:
    HABILITACION = 'habilitacion'
    PRODUCCION = 'produccion'
```

---

## facho.facho

Core de la libreria.

### FachoXML

Abstraccion para manipulacion de XML.

```python
class FachoXML:
    def set_element(xpath, value)
    def get_element(xpath)
    def add_extension(extension)
    def tostring() -> bytes
```

### LXMLBuilder

Constructor de elementos XML usando lxml.

```python
class LXMLBuilder:
    def build() -> Element
```

---

## Codelists

Los codelists se encuentran en `facho.fe.data.dian.codelist`:

- `TipoDocumento` - Tipos de documento electronico
- `TipoImpuesto` - Codigos de impuestos
- `TipoMoneda` - Codigos de moneda
- `Municipio` - Municipios de Colombia
- `Departamento` - Departamentos de Colombia
- `Paises` - Paises
- `MediosPago` - Medios de pago
- `TipoIdFiscal` - Tipos de identificacion fiscal
- `TipoResponsabilidad` - Responsabilidades fiscales
- `TipoOrganizacion` - Tipos de organizacion
- `UnidadesMedida` - Unidades de medida
- `CodigoPrecioReferencia` - Codigos de precio
- `CodigoDescuento` - Codigos de descuento
- `TipoOperacionF` - Tipos de operacion (facturas)
- `TipoOperacionNC` - Tipos de operacion (notas credito)
- `TipoOperacionND` - Tipos de operacion (notas debito)
- `TipoOperacionDS` - Tipos de operacion (documentos soporte)
- `TipoOperacionNCDS` - Tipos de operacion (NC documento soporte)
- `ConceptoNotaCredito` - Conceptos de nota credito
- `ConceptoNotaDebito` - Conceptos de nota debito
