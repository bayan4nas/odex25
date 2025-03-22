{
    'name': 'Custom Invoice Report',
    'version': '14.0.1.0.0',
    'category': 'Accounting',
    'depends': [ 'account'],
    'data': [
        'views/invoice_report_template.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            '/report_e_invoice/static/src/img/logo-tarahum.jpg',
            '/report_e_invoice/static/src/img/vision_2030_header.jpg',
        ],
    },
    'installable': True,
    'application': False,
}