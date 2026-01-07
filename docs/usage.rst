=====
Uso
=====

Esta es la guia de uso de Facho. Para documentacion mas detallada, ver **USAGE.md** en la raiz del proyecto.

Conceptos Basicos
=================

Facho esta organizado en los siguientes modulos principales:

* ``facho.fe.form``: Modelos de datos (Invoice, Party, Amount, etc.)
* ``facho.fe.form_xml``: Generadores de XML (DIANInvoiceXML, etc.)
* ``facho.fe.fe``: Extensiones DIAN (CUFE, firma, etc.)
* ``facho.fe.client.dian``: Cliente para servicios web DIAN

Flujo de Trabajo
----------------

1. **Modelar** el documento usando ``facho.fe.form``
2. **Configurar extensiones** DIAN usando ``facho.fe.fe``
3. **Generar XML** usando ``facho.fe.form_xml``
4. **Firmar** el documento
5. **Enviar** a DIAN (opcional)

Ejemplo Basico
==============

Factura de Venta Nacional
-------------------------

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

    # Metodo de pago
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

Tipos de Documentos
===================

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

Validacion
==========

Facho valida automaticamente los datos contra los codelists oficiales de la DIAN:

.. code-block:: python

    import facho.fe.form as form

    # Validacion automatica al crear objetos
    try:
        city = form.City('99999', 'Ciudad Invalida')
    except ValueError as e:
        print(f"Error: {e}")

CLI
===

Facho incluye una herramienta de linea de comandos::

    # Ver ayuda
    facho --help

    # Generar factura desde archivo Python
    facho generate factura.py

    # Firmar documento
    facho sign documento.xml --key cert.p12 --password clave

    # Enviar a DIAN
    facho send documento.xml --env habilitacion

Referencias
===========

* **USAGE.md** - Guia de uso completa
* **docs/API.md** - Referencia de la API
* **docs/ANEXO_TECNICO_V19.md** - Cambios del Anexo v1.9
* **examples/** - Ejemplos de uso
