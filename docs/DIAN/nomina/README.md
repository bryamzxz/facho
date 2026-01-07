# Nomina Electronica - Documentacion DIAN

Este directorio contiene la documentacion oficial de la DIAN para la implementacion de Nomina Electronica.

## Archivos Incluidos

| Archivo | Descripcion |
|---------|-------------|
| `Resolucion 000013 de 11-02-2021.pdf` | Resolucion que reglamenta la nomina electronica |
| `Anexo Tecnico 11-02-2021.pdf` | Anexo tecnico con especificaciones XML |
| `Caja-de-Herramientas-Nomina-Electronica-V1-0.zip` | XSD, codelists y ejemplos oficiales |

## CUNE (Codigo Unico de Nomina Electronica)

El CUNE se genera segun la seccion 8.1.1.1 del archivo `Resolucion 000013 de 11-02-2021.pdf`.

### Componentes del CUNE

1. Numero del documento
2. Fecha de generacion
3. Hora de generacion
4. Valor total devengado
5. Valor total deducido
6. Valor total comprobante
7. NIT del empleador
8. Numero de documento del trabajador
9. Tipo de documento del trabajador
10. Software-Pin
11. Ambiente

### Algoritmo

El CUNE se calcula usando SHA-384 sobre la concatenacion de los componentes.

## Estructura del Documento XML

La nomina electronica sigue el esquema UBL 2.1 con extensiones DIAN:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NominaIndividual xmlns="dian:gov:co:facturaelectronica:NominaIndividual">
    <Periodo>...</Periodo>
    <NumeroSecuenciaXML>...</NumeroSecuenciaXML>
    <LugarGeneracionXML>...</LugarGeneracionXML>
    <InformacionGeneral>...</InformacionGeneral>
    <Empleador>...</Empleador>
    <Trabajador>...</Trabajador>
    <Pago>...</Pago>
    <FechasPagos>...</FechasPagos>
    <Devengados>...</Devengados>
    <Deducciones>...</Deducciones>
    <Totales>...</Totales>
</NominaIndividual>
```

## Implementacion en Facho

Facho implementa la nomina electronica en el modulo `facho.fe.nomina`:

```python
from facho.fe.nomina import (
    NominaIndividual,
    Empleador,
    Trabajador,
    Devengado,
    Deduccion,
    Pago
)
```

### Ejemplo Basico

```python
from facho.fe.nomina import NominaIndividual
from facho.fe.nomina.devengado import Basico, Transporte
from facho.fe.nomina.deduccion import Salud, FondoPension

# Crear nomina
nomina = NominaIndividual()

# Configurar periodo
nomina.set_periodo(
    fecha_ingreso='2020-01-15',
    fecha_liquidacion_inicio='2024-01-01',
    fecha_liquidacion_fin='2024-01-31',
    tiempo_laborado=30
)

# Configurar empleador
nomina.set_empleador(
    razon_social='MI EMPRESA SAS',
    nit='900123456',
    dv='7',
    pais='CO',
    departamento='05',
    municipio='05001',
    direccion='Calle 123 #45-67'
)

# Configurar trabajador
nomina.set_trabajador(
    tipo_documento='13',
    numero_documento='1234567890',
    nombres='JUAN',
    apellidos='PEREZ GARCIA',
    tipo_contrato='1',
    salario=2000000.00,
    codigo_trabajador='001'
)

# Agregar devengados
nomina.add_devengado(Basico(
    dias_trabajados=30,
    sueldo_trabajado=2000000.00
))
nomina.add_devengado(Transporte(
    auxilio_transporte=140606.00
))

# Agregar deducciones
nomina.add_deduccion(Salud(
    porcentaje=4.0,
    deduccion=80000.00
))
nomina.add_deduccion(FondoPension(
    porcentaje=4.0,
    deduccion=80000.00
))

# Calcular y generar
nomina.calculate()
```

## Enlaces Oficiales

- [Portal Nomina Electronica DIAN](https://www.dian.gov.co/impuestos/Paginas/Sistema-de-Factura-Electronica/documento-soporte-de-pago-de-nomina-electronica.aspx)
- [Caja de Herramientas](https://www.dian.gov.co/impuestos/factura-electronica/)

## Proyectos Relacionados

- [presik/electronic_payroll](https://bitbucket.org/presik/electronic_payroll.git)
- [presik/trytonpsk-staff_payroll_co](https://bitbucket.org/presik/trytonpsk-staff_payroll_co.git)

## Notas

- Se extrae documento tecnico de resolucion usando **pdfarranger**
- Ver seccion 8.1.1.1 del archivo `Resolucion 000013 de 11-02-2021.pdf` para detalles del CUNE
