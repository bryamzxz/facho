# Deducciones - Nomina Electronica

Este modulo contiene las clases para representar las deducciones en la nomina electronica.

## Descripcion

Las deducciones son los descuentos que se aplican al salario del trabajador. Incluyen:

- **Salud**: Aporte a EPS del trabajador
- **Pension**: Aporte a fondo de pensiones del trabajador
- **Otras deducciones**: Libranzas, embargos, retenciones, etc.

## Clases Disponibles

### Salud

Aporte a salud (EPS) del trabajador.

```python
from facho.fe.nomina.deduccion import Salud

salud = Salud(
    porcentaje=4.0,
    deduccion=80000.00
)
```

### FondoPension

Aporte a fondo de pensiones del trabajador.

```python
from facho.fe.nomina.deduccion import FondoPension

pension = FondoPension(
    porcentaje=4.0,
    deduccion=80000.00
)
```

### Deduccion (Base)

Clase base para otras deducciones.

```python
from facho.fe.nomina.deduccion import Deduccion

deduccion = Deduccion(
    tipo='Libranza',
    valor=150000.00
)
```

## Estructura de una Deduccion

Todas las deducciones deben tener:

- Un porcentaje o valor fijo
- El monto de la deduccion calculado
- Referencia al tipo de deduccion segun codelist DIAN

## Contribuir

Para agregar nuevos tipos de deducciones:

1. Crear nuevo objeto de valor en un archivo Python
2. Exportar en `__init__.py` atributo `__all__`
3. Seguir la estructura de las clases existentes
4. Agregar tests correspondientes

## Referencias

- [Anexo Tecnico Nomina Electronica DIAN](https://www.dian.gov.co/impuestos/Paginas/Sistema-de-Factura-Electronica/documento-soporte-de-pago-de-nomina-electronica.aspx)
- Resolucion 000013 de 11-02-2021
