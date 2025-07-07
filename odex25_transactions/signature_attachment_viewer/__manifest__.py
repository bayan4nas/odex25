{
    'name': 'Signature Attachment Viewer',
    'version': '14.0.1',
    'category': 'Services/Tools',
    'author': 'اسمك',
    'website': 'رابطك إن وجد',
    'support': 'بريدك',
    'sequence': 2,
    'summary': """Widget to preview signature attachments easily.""",
    'description': """ Preview signature documents/attachments without download. """,
    'price': 0,
    'currency': 'USD',
    'depends': ['size_restriction_for_attachments'],
    'data': ['views/assets.xml'],
    "qweb": [
        "static/src/xml/odx_document_viewer_legacy.xml",
        "static/src/xml/odx_many2many_attachment_preview.xml",
    ],
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'images': ['static/description/thumbnail2.gif'],

'assets': {
    'web.assets_backend': [
        'signature_attachment_viewer/static/src/js/jquery-ui.js',
        'signature_attachment_viewer/static/css/jquery-ui.css',
        'signature_attachment_viewer/static/src/js/pdf.js',
        'signature_attachment_viewer/static/src/js/pdf.worker.js',

    ],
},

}