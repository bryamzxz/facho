=====
Facho
=====

.. image:: logo.svg
   :alt: Facho Logo
   :width: 200

**Facho** es una libreria Python open-source para facturacion electronica en Colombia (DIAN).

Implementa el estandar UBL 2.1 y XAdES-EPES para la generacion de facturas electronicas,
notas credito/debito, documentos soporte y nomina electronica segun el Anexo Tecnico de la DIAN.

Caracteristicas
===============

* Generacion de Facturas Electronicas de Venta (FE)
* Notas Credito y Debito
* Documentos Soporte (para adquisiciones a no obligados)
* Nomina Electronica
* Firma digital XAdES-EPES con politica DIAN v2
* Calculo automatico de CUFE/CUDE (SHA-384)
* Cliente para servicios web DIAN (habilitacion y produccion)
* Validacion contra codelists oficiales DIAN
* CLI para generacion y envio de documentos

Compatibilidad
==============

* Anexo Tecnico de Factura Electronica de Venta v1.9 (Resolucion 000165/2023)
* Anexo Tecnico de Nomina Electronica v1.0
* Python 3.8+

Estructura del Proyecto
=======================

.. code-block:: text

    facho/
    ├── __init__.py
    └── fe/                       # Facturacion Electronica
        ├── __init__.py
        ├── builders/             # Constructores XML UBL 2.1
        │   ├── invoice_builder.py    # InvoiceBuilder, Party, Address
        │   ├── credit_note_builder.py # CreditNoteBuilder
        │   ├── debit_note_builder.py  # DebitNoteBuilder
        │   └── constants.py          # Constantes DIAN
        ├── client/               # Cliente DIAN
        │   └── dian.py           # DianClient
        ├── signing/              # Firma digital
        │   └── xades.py          # XAdESSigner
        └── data/dian/            # Datos estaticos DIAN
            └── codelist/         # Listas de codigos (.gc)

    dian_fe/                      # Paquete modular independiente
    ├── __init__.py
    ├── xml_builder.py            # InvoiceBuilder, CreditNoteBuilder, DebitNoteBuilder
    ├── xades_signer.py           # XAdESSigner
    ├── dian_client.py            # DianClient
    ├── certificate.py            # Manejo de certificados
    ├── utils.py                  # CUFE, CUDE, DV
    └── config.py                 # Configuracion

Instalacion
===========

Usando pip desde GitHub::

    pip install git+https://github.com/bit4bit/facho

Desde codigo fuente::

    git clone https://github.com/bit4bit/facho
    cd facho
    pip install -e .

Con dependencias de desarrollo::

    pip install -e ".[dev]"

Uso Rapido
==========

Ejemplo basico de generacion de factura usando el paquete modular ``dian_fe``:

.. code-block:: python

    from dian_fe import (
        InvoiceBuilder, InvoiceConfig, Party, Address, InvoiceLine,
        XAdESSigner, DianClient
    )

    # Configuracion
    config = InvoiceConfig(
        software_id='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        software_pin='12345',
        technical_key='clave_tecnica_dian',
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
        tax_scheme='O-48',
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
        nit='1234567890',
        dv='',
        name='CLIENTE EJEMPLO',
        doc_type='13',  # Cedula
        tax_scheme='O-49',
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
            quantity=1,
            unit_code='94',
            description='Producto de ejemplo',
            price=100000.00,
            tax_percent=19.0
        )
    ]

    # Crear factura
    builder = InvoiceBuilder(config)
    xml = builder.build(
        number='SETP990003033',
        issue_date='2026-01-08',
        issue_time='10:30:00-05:00',
        supplier=supplier,
        customer=customer,
        lines=lines
    )

    # Firmar
    signer = XAdESSigner.from_pkcs12('certificado.p12', 'password')
    signed_xml = signer.sign(xml)

    # Guardar
    with open('factura_firmada.xml', 'wb') as f:
        f.write(signed_xml)

Linea de Comandos (CLI)
=======================

Facho incluye una herramienta de linea de comandos::

    # Ver ayuda
    facho --help

    # Generar factura desde especificacion Python
    facho generate invoice.py

    # Firmar documento XML
    facho sign documento.xml --key certificado.p12 --password clave

    # Enviar a DIAN
    facho send documento.xml --env habilitacion

Tipos de Documentos Soportados
==============================

+------------------------+--------+-----------------------------------+
| Documento              | Codigo | Clase                             |
+========================+========+===================================+
| Factura de Venta       | 01     | NationalSalesInvoice              |
+------------------------+--------+-----------------------------------+
| Nota Credito           | 91     | CreditNote                        |
+------------------------+--------+-----------------------------------+
| Nota Debito            | 92     | DebitNote                         |
+------------------------+--------+-----------------------------------+
| Documento Soporte      | 05     | SupportDocument                   |
+------------------------+--------+-----------------------------------+
| NC Documento Soporte   | 95     | SupportDocumentCreditNote         |
+------------------------+--------+-----------------------------------+

Codigos de Impuestos
====================

+--------+-------+-------------------------------------------+
| Codigo | Sigla | Descripcion                               |
+========+=======+===========================================+
| 01     | IVA   | Impuesto al Valor Agregado                |
+--------+-------+-------------------------------------------+
| 02     | IC    | Impuesto al Consumo                       |
+--------+-------+-------------------------------------------+
| 03     | ICA   | Impuesto de Industria y Comercio          |
+--------+-------+-------------------------------------------+
| 04     | INC   | Impuesto Nacional al Consumo              |
+--------+-------+-------------------------------------------+
| 05     | ReteIVA | Retencion IVA                           |
+--------+-------+-------------------------------------------+
| 06     | ReteFte | Retencion en la Fuente                  |
+--------+-------+-------------------------------------------+
| 07     | ReteICA | Retencion ICA                           |
+--------+-------+-------------------------------------------+
| 08     | IC%   | Impuesto al Consumo (porcentual)          |
+--------+-------+-------------------------------------------+
| 20     | FtoHorticultura | Cuota de Fomento Hortofruticola |
+--------+-------+-------------------------------------------+
| 21     | Timbre | Impuesto de Timbre                       |
+--------+-------+-------------------------------------------+
| 22     | INC Bolsas | Impuesto Bolsas Plasticas            |
+--------+-------+-------------------------------------------+
| 23     | INCarbono | Impuesto Nacional Carbono            |
+--------+-------+-------------------------------------------+
| 24     | INCombustibles | Impuesto Combustibles            |
+--------+-------+-------------------------------------------+
| 25     | Sobretasa Comb | Sobretasa Combustibles           |
+--------+-------+-------------------------------------------+
| 26     | Sordicom | Aporte Significativo                   |
+--------+-------+-------------------------------------------+
| 32     | ICL   | Impuesto al Consumo de Licores            |
+--------+-------+-------------------------------------------+
| 33     | INPP  | Impuesto Nacional Productos Plasticos     |
+--------+-------+-------------------------------------------+
| 34     | IBUA  | Impuesto Bebidas Ultraprocesadas          |
+--------+-------+-------------------------------------------+
| 35     | ICUI  | Impuesto Comestibles Ultraprocesados      |
+--------+-------+-------------------------------------------+
| 36     | ADV   | Ad Valorem                                |
+--------+-------+-------------------------------------------+
| ZZ     | Otros | Nombre del Tributo segun Anexo           |
+--------+-------+-------------------------------------------+

Conceptos de Nota Credito
=========================

Segun Anexo Tecnico v1.9 (codigo 5 "Otros" fue eliminado):

+--------+-------------------------------------------------------+
| Codigo | Descripcion                                           |
+========+=======================================================+
| 1      | Devolucion de parte de los bienes; no aceptacion      |
+--------+-------------------------------------------------------+
| 2      | Anulacion de factura electronica                      |
+--------+-------------------------------------------------------+
| 3      | Rebaja o descuento parcial o total                    |
+--------+-------------------------------------------------------+
| 4      | Ajuste de precio                                      |
+--------+-------------------------------------------------------+
| 6      | Descuento comercial por pronto pago                   |
+--------+-------------------------------------------------------+
| 7      | Descuento comercial por volumen de ventas             |
+--------+-------------------------------------------------------+

**Nota:** El codigo 5 "Otros" fue eliminado en el Anexo Tecnico v1.9.

Tests
=====

Ejecutar tests::

    pytest tests/ -v

Ejecutar tests con cobertura::

    pytest tests/ --cov=facho --cov-report=html

Contribuir
==========

Las contribuciones son bienvenidas. Ver **CONTRIBUTING.rst** para mas detalles.

1. Fork del repositorio
2. Crear rama de feature (``git checkout -b feature/mi-feature``)
3. Commit de cambios (``git commit -am 'Agregar mi feature'``)
4. Push a la rama (``git push origin feature/mi-feature``)
5. Crear Pull Request

Desarrollo con Docker
---------------------

::

    make -f Makefile.dev dev-setup
    make -f Makefile.dev dev-shell
    make -f Makefile.dev test

Documentacion
=============

La documentacion completa esta disponible en:

* **USAGE.md** - Guia de uso detallada
* **dian_fe/README.md** - Documentacion del paquete modular
* **docs/ANEXO_TECNICO_V19.md** - Cambios del Anexo Tecnico v1.9
* **examples/** - Ejemplos de uso

Referencias DIAN
================

* `Anexo Tecnico v1.9 <https://www.dian.gov.co/impuestos/factura-electronica/Documents/Anexo-Tecnico-Factura-Electronica-de-Venta-vr-1-9.pdf>`_
* `Caja de Herramientas v1.9 <https://www.dian.gov.co/impuestos/factura-electronica/Paginas/Factura-Electronica.aspx>`_
* `Portal Factura Electronica DIAN <https://www.dian.gov.co/impuestos/factura-electronica/>`_
* `Nomina Electronica DIAN <https://www.dian.gov.co/impuestos/Paginas/Sistema-de-Factura-Electronica/documento-soporte-de-pago-de-nomina-electronica.aspx>`_

Licencia
========

Este proyecto esta licenciado bajo los terminos de la licencia que se encuentra
en el archivo **LICENSE**.

Autores
=======

Ver **AUTHORS.rst** para la lista de contribuidores.
