# -*- coding: utf-8 -*-
# This file is part of facho.
"""
CLI para facturacion electronica DIAN Colombia.
Usa los modulos simplificados sin dependencias legacy.
"""

import sys
import click


@click.command()
@click.option('--cert', required=True, type=click.Path(exists=True), help='Certificado .pfx')
@click.option('--password', required=True, help='Password del certificado')
@click.option('--habilitacion/--produccion', default=True, help='Ambiente')
@click.option('--track-id', required=True, help='ZipKey o TrackId')
def get_status_zip(cert, password, habilitacion, track_id):
    """Consultar estado de documento por ZipKey."""
    from facho.fe.client import DianSimpleClient

    environment = 'habilitacion' if habilitacion else 'produccion'
    client = DianSimpleClient(
        certificate_path=cert,
        certificate_password=password,
        environment=environment
    )

    resp = client.get_status_zip(track_id)

    click.echo(f"ZipKey: {track_id}")
    click.echo(f"IsValid: {resp.is_valid}")
    click.echo(f"StatusCode: {resp.status_code}")
    click.echo(f"StatusDescription: {resp.status_description}")

    if resp.error_messages:
        click.echo("=== ERRORES ===")
        for msg in resp.error_messages:
            click.echo(f"  * {msg}")


@click.command()
@click.option('--cert', required=True, type=click.Path(exists=True), help='Certificado .pfx')
@click.option('--password', required=True, help='Password del certificado')
@click.option('--habilitacion/--produccion', default=True, help='Ambiente')
@click.option('--test-set-id', required=True, help='TestSetId DIAN')
@click.argument('filename', required=True)
@click.argument('zipfile', type=click.Path(exists=True))
def send_test_set_async(cert, password, habilitacion, test_set_id, filename, zipfile):
    """Enviar documento de prueba a DIAN."""
    from facho.fe.client import DianSimpleClient

    environment = 'habilitacion' if habilitacion else 'produccion'
    client = DianSimpleClient(
        certificate_path=cert,
        certificate_password=password,
        environment=environment
    )

    with open(zipfile, 'rb') as f:
        content = f.read()

    resp = client.send_test_set_async(filename, content, test_set_id)

    click.echo(f"ZipKey: {resp.zip_key}")
    if resp.error_messages:
        click.echo("=== ERRORES ===")
        for msg in resp.error_messages:
            click.echo(f"  * {msg}")


@click.command()
@click.option('--cert', required=True, type=click.Path(exists=True), help='Certificado .pfx')
@click.option('--password', required=True, help='Password del certificado')
@click.option('--habilitacion/--produccion', default=True, help='Ambiente')
@click.argument('filename', required=True)
@click.argument('zipfile', type=click.Path(exists=True))
def send_bill_sync(cert, password, habilitacion, filename, zipfile):
    """Enviar documento sincronicamente a DIAN."""
    from facho.fe.client import DianSimpleClient

    environment = 'habilitacion' if habilitacion else 'produccion'
    client = DianSimpleClient(
        certificate_path=cert,
        certificate_password=password,
        environment=environment
    )

    with open(zipfile, 'rb') as f:
        content = f.read()

    resp = client.send_bill_sync(filename, content)

    click.echo(f"IsValid: {resp.is_valid}")
    click.echo(f"StatusCode: {resp.status_code}")
    click.echo(f"StatusDescription: {resp.status_description}")

    if resp.error_messages:
        click.echo("=== ERRORES ===")
        for msg in resp.error_messages:
            click.echo(f"  * {msg}")


@click.command()
@click.option('--cert', required=True, type=click.Path(exists=True), help='Certificado .pfx')
@click.option('--password', required=True, help='Password del certificado')
@click.argument('xmlfile', type=click.Path(exists=True), required=True)
@click.argument('output', required=True)
def sign_xml(cert, password, xmlfile, output):
    """Firmar documento XML con XAdES-EPES."""
    from facho.fe.signing import XAdESSigner
    from lxml import etree

    signer = XAdESSigner.from_pkcs12(cert, password)

    with open(xmlfile, 'rb') as f:
        xml_content = f.read()

    xml = etree.fromstring(xml_content)
    signed_xml = signer.sign(xml)

    with open(output, 'wb') as f:
        f.write(etree.tostring(signed_xml, encoding='UTF-8', xml_declaration=True))

    click.echo(f"Documento firmado guardado en: {output}")


@click.command()
def version():
    """Mostrar version."""
    click.echo("facho v0.1.0 - Facturacion Electronica DIAN Colombia")


@click.group()
def main():
    """CLI para facturacion electronica DIAN Colombia."""
    pass


main.add_command(get_status_zip)
main.add_command(send_test_set_async)
main.add_command(send_bill_sync)
main.add_command(sign_xml)
main.add_command(version)
