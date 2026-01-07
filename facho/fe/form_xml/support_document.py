from .. import fe
from ..form import *
from .invoice import DIANInvoiceXML

__all__ = ['DIANSupportDocumentXML']


class DIANSupportDocumentXML(DIANInvoiceXML):
    """
    DIANSupportDocumentXML mapea objeto form.SupportDocument a XML segun
    lo indicado para el Documento Soporte en adquisiciones efectuadas
    a sujetos no obligados a expedir factura.
    """

    def __init__(self, document):
        super(DIANSupportDocumentXML, self).__init__(document, 'Invoice')

    def tag_document(fexml):
        return 'Invoice'

    def tag_document_concilied(fexml):
        return 'Invoiced'

    def post_attach_invoice(fexml, invoice):
        fexml.set_element('./cbc:ProfileID', 'DIAN 2.1: documento soporte en adquisiciones efectuadas a no obligados a facturar.')

    def set_withholding_tax_total(fexml, document):
        """Establece los totales de retenciones (WithholdingTaxTotal)"""
        if not hasattr(document, 'invoice_withholding_tax_total'):
            return

        for withholding in document.invoice_withholding_tax_total:
            line = fexml.fragment('./cac:WithholdingTaxTotal', append=True)
            fexml.set_element_amount_for(line,
                                         '/cac:WithholdingTaxTotal/cbc:TaxAmount',
                                         withholding.tax_amount)

            for subtotal in withholding.subtotals:
                fexml.set_element_amount_for(line,
                                             '/cac:WithholdingTaxTotal/cac:TaxSubtotal/cbc:TaxableAmount',
                                             subtotal.taxable_amount)
                fexml.set_element_amount_for(line,
                                             '/cac:WithholdingTaxTotal/cac:TaxSubtotal/cbc:TaxAmount',
                                             subtotal.tax_amount)
                if subtotal.percent is not None:
                    line.set_element('/cac:WithholdingTaxTotal/cac:TaxSubtotal/cbc:Percent',
                                     '%0.2f' % round(subtotal.percent, 2))
                if subtotal.scheme is not None:
                    line.set_element('/cac:WithholdingTaxTotal/cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:ID',
                                     subtotal.scheme.code)
                    line.set_element('/cac:WithholdingTaxTotal/cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:Name',
                                     subtotal.scheme.name)

    def attach_invoice(fexml, invoice):
        """Adiciona etiquetas a FEXML para documento soporte"""
        super(DIANSupportDocumentXML, fexml).attach_invoice(invoice)
        fexml.set_withholding_tax_total(invoice)
        return fexml
