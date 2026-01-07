# Cambios del Anexo Tecnico v1.9 (Resolucion 000165/2023)

Este documento describe los cambios principales del Anexo Tecnico de Factura Electronica de Venta version 1.9 de la DIAN y su implementacion en Facho.

## Tabla de Contenidos

- [Resumen de Cambios](#resumen-de-cambios)
- [Nuevas Reglas de Validacion](#nuevas-reglas-de-validacion)
- [Nuevos Tributos](#nuevos-tributos)
- [Cambios en Conceptos de Nota Credito](#cambios-en-conceptos-de-nota-credito)
- [Cambios en Tipos de Documento](#cambios-en-tipos-de-documento)
- [Nuevos Servicios Web](#nuevos-servicios-web)
- [Control Cambiario](#control-cambiario)
- [Estado de Implementacion](#estado-de-implementacion)

## Resumen de Cambios

El Anexo Tecnico v1.9 introduce las siguientes modificaciones principales:

1. **Nuevos codigos de tributos** (INPP, IBUA, ICUI, ICL, ADV)
2. **Nuevas reglas de validacion** (FAJ43a, FAJ43b, etc.)
3. **Modificaciones en conceptos de notas credito** (eliminacion codigo 5)
4. **Nuevos tipos de documento de identificacion** (PPT)
5. **Nuevos servicios web** (GetStatusEvent, GetReferenceNotes)
6. **Modos de control cambiario** para compra/venta de divisas

## Nuevas Reglas de Validacion

### Validacion de Nombre vs RUT

| Regla | Descripcion | Severidad |
|-------|-------------|-----------|
| FAJ43a | Validar que el nombre del emisor coincida con el RUT | Notificacion |
| FAJ43b | Validar que el nombre del adquirente coincida con el RUT | Notificacion |

**Detalles de validacion:**
- NO sensible a mayusculas/minusculas
- SI sensible a acentos y tildes
- SI sensible a espacios adicionales
- El nombre debe coincidir exactamente con el registrado en el RUT

```python
# Ejemplo: Espacios adicionales causaran notificacion
# Incorrecto: "MI  EMPRESA  SAS" (espacios dobles)
# Correcto: "MI EMPRESA SAS"
```

### Validacion de Fechas

| Regla | Descripcion | Severidad |
|-------|-------------|-----------|
| FAD09e | Fecha de elaboracion = Fecha de envio | Rechazo |
| CAD09e | Fecha de elaboracion NC = Fecha de envio | Rechazo |
| DAD09e | Fecha de elaboracion ND = Fecha de envio | Rechazo |

### Otras Validaciones

| Regla | Descripcion |
|-------|-------------|
| FAD01 | UBLVersionID debe ser "UBL 2.1" |
| FAD02 | CustomizationID debe coincidir con tipo de operacion |
| FAD05 | ID (prefijo + consecutivo) debe estar en rango autorizado |
| FAD16 | LineCountNumeric debe coincidir con numero real de lineas |

## Nuevos Tributos

El Anexo v1.9 agrega los siguientes codigos de tributos:

| Codigo | Sigla | Nombre Completo |
|--------|-------|-----------------|
| 32 | INPP | Impuesto Nacional al consumo de Productos Plasticos de un solo uso |
| 33 | IBUA | Impuesto a las Bebidas Ultraprocesadas Azucaradas |
| 34 | ICUI | Impuesto al consumo de productos Comestibles Ultraprocesados Industrialmente |
| 35 | ICL | Impuesto al Consumo de Licores, vinos, aperitivos y similares |
| 36 | ADV | Ad Valorem |

### Uso en Facho

```python
import facho.fe.form as form

# Ejemplo con impuesto INPP
inv.add_invoice_line(form.InvoiceLine(
    quantity=form.Quantity(100, '94'),
    description='Bolsas plasticas',
    item=form.StandardItem('BOLSA001', 'Bolsas plasticas'),
    price=form.Price(
        amount=form.Amount(50.00),
        type_code='01',
        type='Precio unitario'
    ),
    tax=form.TaxTotal(
        subtotals=[
            form.TaxSubTotal(
                percent=19.00,
                scheme=form.TaxScheme('01')  # IVA
            ),
            form.TaxSubTotal(
                percent=0.00,  # INPP es por unidad, no porcentaje
                scheme=form.TaxScheme('32')  # INPP
            )
        ]
    )
))
```

### Tarifas de Nuevos Tributos

| Tributo | Tipo | Valor |
|---------|------|-------|
| INPP | Por unidad | Variable segun producto |
| IBUA | Porcentaje | Variable segun contenido de azucar |
| ICUI | Porcentaje | Variable segun producto |
| ICL | Por unidad/grado | Variable segun grado alcoholimetrico |
| ADV | Porcentaje | Variable |

## Cambios en Conceptos de Nota Credito

**IMPORTANTE:** El codigo 5 "Otros" fue **eliminado** en el Anexo v1.9.

### Conceptos Vigentes

| Codigo | Descripcion |
|--------|-------------|
| 1 | Devolucion parcial de los bienes y/o no aceptacion parcial del servicio |
| 2 | Anulacion de factura electronica |
| 3 | Rebaja o descuento parcial o total |
| 4 | Ajuste de precio |
| 6 | Otros |

**Nota:** El codigo **5** ya no es valido. Usar codigo **6** para "Otros".

### Conceptos de Nota Debito

| Codigo | Descripcion |
|--------|-------------|
| 1 | Intereses |
| 2 | Gastos por cobrar |
| 3 | Cambio del valor |
| 4 | Otros |

## Cambios en Tipos de Documento

### Nuevo Tipo de Identificacion

| Codigo | Descripcion |
|--------|-------------|
| 48 | PPT (Permiso por Proteccion Temporal) |

Este tipo se agrega a la lista existente de tipos de identificacion fiscal.

### Tipos de Documento Electronico

| Codigo | Descripcion |
|--------|-------------|
| 01 | Factura de Venta |
| 02 | Factura de Exportacion |
| 03 | Factura por Contingencia Facturador |
| 04 | Factura por Contingencia DIAN |
| 05 | Documento Soporte |
| 91 | Nota Credito |
| 92 | Nota Debito |
| 95 | Nota Credito Documento Soporte |

## Nuevos Servicios Web

### GetStatusEvent

Consulta el estado de eventos de un documento:

```python
# Endpoint: https://vpfe.dian.gov.co/WcfDianCustomerServices.svc
# Metodo: GetStatusEvent(trackId)
```

### GetReferenceNotes

Consulta notas credito/debito asociadas a una factura:

```python
# Endpoint: https://vpfe.dian.gov.co/WcfDianCustomerServices.svc
# Metodo: GetReferenceNotes(cufe)
```

**Nota:** Estos servicios aun no estan implementados en Facho.

## Control Cambiario

El Anexo v1.9 define nuevos modos de operacion para control cambiario:

| Modo | Descripcion |
|------|-------------|
| 50 | Compra de divisas |
| 51 | Venta de divisas |

### Uso en Facturas de Exportacion

```python
import facho.fe.form as form

# Factura de exportacion con moneda extranjera
inv = form.NationalSalesInvoice()
inv.set_operation_type('04')  # Exportacion

# Establecer moneda del documento
inv.set_document_currency(form.Currency('USD'))

# Establecer tasa de cambio
inv.set_calculation_rate(4200.00)  # COP por USD
```

## Estado de Implementacion

### Implementado en Facho

| Caracteristica | Estado | Notas |
|----------------|--------|-------|
| Estructura UBL 2.1 | OK | Completo |
| Namespaces DIAN | OK | Completo |
| CUFE/CUDE SHA-384 | OK | Completo |
| Extensiones DIAN | OK | Completo |
| Firma XAdES-EPES | OK | Politica v2 |
| Cliente WS-Security | OK | Completo |
| Listas de codigos | OK | Actualizado v1.9 |
| Timezone Colombia | OK | UTC-05:00 |
| Nuevos tributos (32-36) | OK | Completo |
| Conceptos NC actualizados | OK | Sin codigo 5 |
| Tipo documento PPT (48) | OK | Agregado |

### Pendiente de Implementacion

| Caracteristica | Estado | Prioridad |
|----------------|--------|-----------|
| Validacion FAJ43a/FAJ43b | Pendiente | Alta |
| GetStatusEvent | Pendiente | Media |
| GetReferenceNotes | Pendiente | Media |
| Control cambiario (modos 50/51) | Pendiente | Baja |
| Sector Salud | No implementado | Baja |
| Sector Transporte | No implementado | Baja |
| Sector Fiduciario | No implementado | Baja |

### Recomendaciones de Validacion Local

Antes de enviar a DIAN, se recomienda validar:

1. **RegistrationName** - Verificar que coincida exactamente con RUT
2. **Fechas** - Fecha de elaboracion = Fecha de envio
3. **LineCountNumeric** - Numero correcto de lineas
4. **Rango de numeracion** - ID dentro del rango autorizado
5. **Tributos** - Usar codigos correctos segun producto

## Referencias

- [Anexo Tecnico v1.9 DIAN (PDF)](https://www.dian.gov.co/impuestos/factura-electronica/Documents/Anexo-Tecnico-Factura-Electronica-de-Venta-vr-1-9.pdf)
- [Caja de Herramientas v1.9](https://www.dian.gov.co/impuestos/factura-electronica/Paginas/Factura-Electronica.aspx)
- [Resolucion 000165 de 2023](https://www.dian.gov.co/)
- [Portal Factura Electronica DIAN](https://www.dian.gov.co/impuestos/factura-electronica/)

## Historial de Cambios

| Version | Fecha | Cambios |
|---------|-------|---------|
| 1.9 | 2023 | Nuevos tributos, FAJ43a/b, eliminacion codigo 5 NC |
| 1.8 | 2021 | Documento Soporte, ajustes menores |
| 1.7 | 2020 | Version base implementada en Facho |
