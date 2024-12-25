{
    "name": "Restriction on Stock Location",

    'version': "14.0",

    'category': 'Odex25-Inventory/Odex25-Inventory',
    "summary": "This app will Restriction on Stock Location.",
    
   'author': 'INKERP',
   
    'website': "http://www.inkerp.com",

    "depends": ['stock'],
    
    "data": [
        "security/security.xml",
        "views/stock_location_view.xml",
    ],

    'images': ['static/description/banner.png'],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}
