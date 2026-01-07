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
    ├── cli.py                    # Interfaz de linea de comandos
    ├── facho.py                  # Core: FachoXML, LXMLBuilder
    └── fe/                       # Facturacion Electronica
        ├── fe.py                 # Core FE: CUFE/CUDE, firmas, extensiones DIAN
        ├── form/
        │   ├── __init__.py       # Modelos de datos: Invoice, Party, Amount, etc.
        │   └── query.py          # Consultas
        ├── form_xml/             # Generadores XML
        │   ├── invoice.py        # DIANInvoiceXML
        │   ├── credit_note.py    # Notas credito
        │   ├── debit_note.py     # Notas debito
        │   ├── support_document.py # Documentos soporte
        │   └── utils.py          # Utilidades
        ├── client/               # Cliente DIAN
        │   ├── dian.py           # DianClient, Habilitacion
        │   └── wsse/
        │       └── signature.py  # Firma WS-Security
        ├── data/dian/            # Datos estaticos DIAN
        │   ├── codelist/         # Listas de codigos (.gc)
        │   └── XSD/              # Esquemas XSD
        └── nomina/               # Nomina electronica

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

Ejemplo basico de generacion de factura:

.. code-block:: python

    import facho.fe.form as form
    import facho.fe.form_xml as form_xml
    from datetime import datetime

    # Crear factura de venta nacional
    inv = form.NationalSalesInvoice()

    # Configurar periodo y emision
    inv.set_period(datetime.now(), datetime.now())
    inv.set_issue(datetime.now())
    inv.set_ident('SETP990003033')
    inv.set_operation_type('10')

    # Configurar proveedor
    inv.set_supplier(form.Party(
        legal_name='MI EMPRESA SAS',
        name='MI EMPRESA SAS',
        ident=form.PartyIdentification('900123456', '7', '31'),
        responsability_code=form.Responsability(['O-07', 'O-09']),
        responsability_regime_code='48',
        organization_code='1',
        email='contacto@miempresa.com',
        address=form.Address(
            name='Direccion principal',
            street='Calle 123 #45-67',
            city=form.City('05001', 'Medellin'),
            country=form.Country('CO', 'Colombia'),
            countrysubentity=form.CountrySubentity('05', 'Antioquia')
        )
    ))

    # Configurar cliente
    inv.set_customer(form.Party(
        legal_name='CLIENTE EJEMPLO',
        name='CLIENTE EJEMPLO',
        ident=form.PartyIdentification('1234567890', '', '13'),
        responsability_code=form.Responsability(['R-99-PN']),
        responsability_regime_code='49',
        organization_code='2',
        email='cliente@ejemplo.com',
        address=form.Address(
            name='',
            street='Carrera 10 #20-30',
            city=form.City('11001', 'Bogota'),
            country=form.Country('CO', 'Colombia'),
            countrysubentity=form.CountrySubentity('11', 'Bogota')
        )
    ))

    # Configurar metodo de pago
    inv.set_payment_mean(form.PaymentMean(
        id='1',
        code='10',
        due_at=datetime.now(),
        payment_id='1'
    ))

    # Agregar linea de factura
    inv.add_invoice_line(form.InvoiceLine(
        quantity=form.Quantity(1, '94'),
        description='Producto de ejemplo',
        item=form.StandardItem('PROD001', 'Producto de ejemplo'),
        price=form.Price(
            amount=form.Amount(100000.00),
            type_code='01',
            type='Precio unitario'
        ),
        tax=form.TaxTotal(
            subtotals=[
                form.TaxSubTotal(percent=19.00)
            ]
        )
    ))

    # Calcular totales
    inv.calculate()

    # Generar XML firmado
    xml = form_xml.DIANInvoiceXML(inv)
    form_xml.utils.DIANWriteSigned(
        xml,
        'factura.xml',
        'ruta/certificado.p12',
        'password'
    )

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

La documentacion completa esta disponible en el directorio ``docs/``:

* **USAGE.rst** - Guia de uso detallada
* **docs/ANEXO_TECNICO_V19.md** - Cambios del Anexo Tecnico v1.9
* **docs/API.md** - Referencia de la API
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
