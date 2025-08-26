{
    'name': 'Web Watermark',
    'version': '14.0.1.0.0',
    'summary': 'Apply watermark on screen',
    'author': 'Saip-IT',
    'license': 'AGPL-3',
    'depends': ['web','hr_base'],
    'data': [
        'views/watermark_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'web_watermark/static/src/js/watemark_government.js',
            'web_watermark/static/src/css/watermark.css',
        ],
    },
    'installable': True,
    'application': False,
}
