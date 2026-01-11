======================================
Bienvenido a la documentacion de Facho
======================================

.. image:: ../logo.svg
   :alt: Facho Logo
   :width: 200

**Facho** es una libreria Python open-source para facturacion electronica en Colombia (DIAN).

Implementa el estandar UBL 2.1 y XAdES-EPES para la generacion de facturas electronicas,
notas credito/debito, documentos soporte y nomina electronica.

Caracteristicas
===============

* Generacion de Facturas Electronicas de Venta (FE)
* Notas Credito y Debito
* Documentos Soporte (para adquisiciones a no obligados)
* Nomina Electronica
* Firma digital XAdES-EPES con politica DIAN v2
* Calculo automatico de CUFE/CUDE (SHA-384)
* Cliente para servicios web DIAN
* Validacion contra codelists oficiales DIAN
* CLI para generacion y envio de documentos

Compatibilidad
==============

* Anexo Tecnico de Factura Electronica de Venta v1.9 (Resolucion 000165/2023)
* Anexo Tecnico de Nomina Electronica v1.0
* Python 3.8+

Inicio Rapido
=============

Instalacion::

    pip install git+https://github.com/bryamzxz/facho

Ejemplo basico::

    import facho.fe.form as form
    import facho.fe.form_xml as form_xml
    from datetime import datetime

    inv = form.NationalSalesInvoice()
    inv.set_issue(datetime.now())
    inv.set_ident('SETP990003033')
    # ... configurar resto ...
    inv.calculate()

    xml = form_xml.DIANInvoiceXML(inv)

Contenido
=========

.. toctree::
   :maxdepth: 2
   :caption: Documentacion:

   installation
   usage

.. toctree::
   :maxdepth: 2
   :caption: Referencia:

   modules

.. toctree::
   :maxdepth: 1
   :caption: Anexos:

   DIAN/nomina/README

Indices y tablas
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Documentacion Adicional
=======================

* **USAGE.md** - Guia de uso detallada
* **docs/ANEXO_TECNICO_V19.md** - Cambios del Anexo Tecnico v1.9
* **docs/API.md** - Referencia de la API
* **examples/** - Ejemplos de uso

Enlaces
=======

* `Repositorio GitHub <https://github.com/bryamzxz/facho>`_
* `Anexo Tecnico v1.9 DIAN <https://www.dian.gov.co/impuestos/factura-electronica/>`_
* `Portal Factura Electronica DIAN <https://www.dian.gov.co/impuestos/factura-electronica/>`_
