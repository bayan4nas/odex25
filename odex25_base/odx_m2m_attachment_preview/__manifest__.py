# -*- coding: utf-8 -*-
{
    'name': 'Attachment Preview',
    'version': '14.0.1',
    'category': 'Services/Tools',
    'author': 'Odox SoftHub LLP',
    'website': 'https://www.odoxsofthub.com',
    'support': 'support@odoxsofthub.com',
    'sequence': 2,
    'summary': """This module adds a new widget, many2many_attachment_preview, which enables the user to view attachments without downloading them.""",
    'description': """ User can preview a document without downloading. """,
    'price': 16,
    'currency': 'USD',
    'depends': ['size_restriction_for_attachments'],
    'data': [
        'views/assets.xml'
    ],

    "qweb": [
        "static/src/xml/odx_document_viewer_legacy.xml",
        "static/src/xml/odx_many2many_attachment_preview.xml",
    ],

    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'images': ['static/description/thumbnail2.gif'],
}
