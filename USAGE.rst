=====
Uso
=====

Guia de Uso de Facho
====================

**Facho** es tanto una libreria para modelar y generar los documentos XML requeridos para la facturacion electronica,
asi como una herramienta de **consola** para facilitar actividades como: generacion de XML a partir de una
especificacion en Python, comprimir y enviar archivos segun el SOAP vigente.

**Facho** esta diseñado para ser usado en conjunto con el documento **Anexo Tecnico de Factura Electronica de Venta v1.9**,
ya que en gran medida sigue la terminologia presente en este.

Para la guia completa de uso ver **USAGE.md**.

Instalacion
-----------

Usando pip desde GitHub::

    pip install git+https://github.com/bit4bit/facho

Desde codigo fuente::

    git clone https://github.com/bit4bit/facho
    cd facho
    pip install -e .

Uso Basico
----------

En terminos generales seria:

1. Modelar la factura usando **facho.fe.form**
2. Instanciar las extensiones requeridas ver **facho.fe.fe**
3. Una vez generado el objeto invoice y las extensiones requeridas se procede a crear el XML

Ejemplo:

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

Validacion
----------

.. code-block:: python

    validator = form.DianResolucion0001Validator()

    if not validator.validate(invoice):
        for error in validator.errors:
            print("ERROR:", error)
        raise RuntimeError("invoice invalid")

    xml = form_xml.DIANInvoiceXML(invoice)
    extensions = module.extensions(invoice)
    for extension in extensions:
        xml.add_extension(extension)

    form_xml.DIANWriteSigned(xml, "factura.xml", "llave privada", "frase")

Para Ejemplos
-------------

Ver directorio **examples/** y **USAGE.md** para documentacion completa.

Linea de Comandos
-----------------

Tambien se provee linea de comandos **facho** para generacion, firmado y envio de documentos::

    facho --help
    facho generate invoice.py
    facho sign documento.xml --key cert.p12 --password clave
    facho send documento.xml --env habilitacion

Referencias
-----------

* **docs/DIAN/Anexo_Tecnico_Factura_Electronica_Vr1_7_2020.pdf** - Anexo Tecnico (version anterior)
* **docs/ANEXO_TECNICO_V19.md** - Cambios del Anexo v1.9
* **docs/API.md** - Referencia de la API
