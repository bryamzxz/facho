from .. import fe
from ..form import *
from .support_document import DIANSupportDocumentXML

__all__ = ['DIANSupportDocumentCreditNoteXML']


class DIANSupportDocumentCreditNoteXML(DIANSupportDocumentXML):
    """
    DIANSupportDocumentCreditNoteXML mapea objeto form.SupportDocumentCreditNote a XML
    segun lo indicado para la Nota Crédito del Documento Soporte.
    """

    def __init__(self, document):
        super(DIANSupportDocumentCreditNoteXML, self).__init__(document)

    def tag_document(fexml):
        return 'CreditNote'

    def tag_document_concilied(fexml):
        return 'Credited'

    def post_attach_invoice(fexml, invoice):
        fexml.set_element('./cbc:ProfileID', 'DIAN 2.1: Nota Crédito de Documento Soporte')
