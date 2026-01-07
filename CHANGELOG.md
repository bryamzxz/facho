# Changelog

Todos los cambios notables de este proyecto seran documentados en este archivo.

El formato esta basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Agregado
- Documentacion completa del proyecto
- Guia de uso detallada (USAGE.md)
- Referencia de API (docs/API.md)
- Documentacion de cambios del Anexo Tecnico v1.9
- READMEs mejorados para modulos de nomina electronica

### Cambiado
- README.rst actualizado con ejemplos y tablas de referencia
- docs/index.rst actualizado con nueva estructura
- USAGE.rst sincronizado con USAGE.md

## [0.2.0] - 2024

### Agregado
- Soporte para Anexo Tecnico v1.9
- Nuevos codigos de tributos (INPP, IBUA, ICUI, ICL, ADV - codigos 32-36)
- Actualizacion de conceptos de Nota Credito (eliminado codigo 5)
- Tipo de documento PPT (codigo 48)
- Clase Currency para soporte multi-moneda
- Metodos para facturas de exportacion
- Validacion de fechas de emision
- Soporte para tasa de cambio en exportaciones
- Clases SupportDocument y SupportDocumentCreditNote
- Clase WithholdingTaxTotal para retenciones

### Cambiado
- Mejorada documentacion de clases con docstrings
- Actualizados codelists segun Caja de Herramientas v1.9
- Corregido codigo de concepto de Nota Credito 'Otros' de 5 a 6

### Corregido
- Correccion de codigos de impuestos segun Anexo 1.9 oficial DIAN
- Eliminacion de codigo 5 'Otros' de ConceptoNotaCredito

## [0.1.0] - 2020

### Agregado
- Primera version de facho
- Soporte para Factura Electronica de Venta (FE)
- Soporte para Notas Credito y Debito
- Generacion de CUFE/CUDE con SHA-384
- Firma digital XAdES-EPES con politica DIAN v2
- Cliente para servicios web DIAN
- Validacion contra codelists oficiales
- CLI para generacion y envio
- Soporte para Nomina Electronica

### Documentacion
- README inicial
- USAGE.rst con ejemplos basicos
- CONTRIBUTING.rst para contribuidores

---

## Tipos de Cambios

- `Agregado` para nuevas caracteristicas
- `Cambiado` para cambios en funcionalidad existente
- `Deprecado` para caracteristicas que seran eliminadas
- `Eliminado` para caracteristicas eliminadas
- `Corregido` para correccion de bugs
- `Seguridad` para vulnerabilidades

## Enlaces

- [Repositorio](https://github.com/bit4bit/facho)
- [Anexo Tecnico v1.9 DIAN](https://www.dian.gov.co/impuestos/factura-electronica/)
