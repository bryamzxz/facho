.. highlight:: shell

============
Instalacion
============

Requisitos
----------

* Python 3.8 o superior
* pip (gestor de paquetes Python)
* Certificado digital (.p12 o .pfx) para firma (opcional, requerido para envio a DIAN)

Dependencias principales:

* lxml - Procesamiento XML
* cryptography - Firma digital
* zeep - Cliente SOAP

Instalacion Rapida
------------------

Usando pip desde GitHub::

    pip install git+https://github.com/bit4bit/facho

Instalacion desde Codigo Fuente
-------------------------------

Clonar el repositorio::

    git clone https://github.com/bit4bit/facho
    cd facho

Crear entorno virtual (recomendado)::

    python3 -m venv venv
    source venv/bin/activate  # Linux/Mac
    # o
    venv\Scripts\activate     # Windows

Instalar en modo desarrollo::

    pip install -e .

Con dependencias de desarrollo::

    pip install -e ".[dev]"

Instalacion con Docker
----------------------

El proyecto incluye soporte para Docker::

    make -f Makefile.dev dev-setup
    make -f Makefile.dev dev-shell

Verificar Instalacion
---------------------

Verificar que facho esta instalado correctamente::

    python -c "import facho; print(facho.__version__)"

O usando el CLI::

    facho --help

Configuracion de Certificado
----------------------------

Para firmar documentos y enviar a DIAN, necesitas un certificado digital:

1. Obtener certificado de una CA reconocida (Certicamara, GSE, etc.)
2. El certificado debe estar en formato PKCS#12 (.p12 o .pfx)
3. Guardar el certificado en una ubicacion segura

Ejemplo de uso::

    from facho.fe.form_xml import utils

    utils.DIANWriteSigned(
        xml,
        'factura_firmada.xml',
        '/ruta/a/certificado.p12',
        'password_del_certificado'
    )

Problemas Comunes
-----------------

Error: lxml no se puede instalar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

En algunos sistemas necesitas instalar dependencias del sistema::

    # Ubuntu/Debian
    sudo apt-get install libxml2-dev libxslt-dev python3-dev

    # CentOS/RHEL
    sudo yum install libxml2-devel libxslt-devel python3-devel

    # macOS
    brew install libxml2 libxslt

Error: cryptography no se puede instalar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instalar dependencias de compilacion::

    # Ubuntu/Debian
    sudo apt-get install build-essential libssl-dev libffi-dev

    # CentOS/RHEL
    sudo yum install gcc openssl-devel libffi-devel

Actualizacion
-------------

Para actualizar a la ultima version::

    pip install --upgrade git+https://github.com/bit4bit/facho

Desinstalacion
--------------

Para desinstalar facho::

    pip uninstall facho

Enlaces
-------

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/
.. _Github repo: https://github.com/bit4bit/facho
