# Devengados - Nomina Electronica

Este modulo contiene las clases para representar los conceptos devengados en la nomina electronica.

## Descripcion

Los devengados son los conceptos que el empleador debe pagar al trabajador. Incluyen:

- **Basico**: Salario basico del trabajador
- **Transporte**: Auxilio de transporte
- **Horas Extras**: Horas extras diurnas, nocturnas, dominicales, festivas

## Clases Disponibles

### Basico

Representa el salario basico del trabajador.

```python
from facho.fe.nomina.devengado import Basico

basico = Basico(
    dias_trabajados=30,
    sueldo_trabajado=2000000.00
)
```

### Transporte

Auxilio de transporte legal.

```python
from facho.fe.nomina.devengado import Transporte

transporte = Transporte(
    auxilio_transporte=140606.00,
    viatico_manutenc_alojamiento=0.00,
    viatico_no_salarial=0.00
)
```

### HorasExtras

Horas extras trabajadas.

```python
from facho.fe.nomina.devengado import HorasExtras

horas_extras = HorasExtras(
    hora_extra_diurna=HoraExtraDiurna(
        cantidad=10,
        pago=125000.00
    ),
    hora_extra_nocturna=HoraExtraNocturna(
        cantidad=5,
        pago=87500.00
    )
)
```

## Contribuir

Para agregar nuevos tipos de devengados:

1. Crear nuevo objeto de valor en un archivo Python
2. Exportar en `__init__.py` atributo `__all__`
3. Seguir la estructura de las clases existentes
4. Agregar tests correspondientes

## Referencias

- [Anexo Tecnico Nomina Electronica DIAN](https://www.dian.gov.co/impuestos/Paginas/Sistema-de-Factura-Electronica/documento-soporte-de-pago-de-nomina-electronica.aspx)
- Resolucion 000013 de 11-02-2021
