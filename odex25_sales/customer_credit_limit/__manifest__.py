
{ 
    "name": "Customer Credit Limit",
    "summary": """Customer Credit Limit""",
    "version": '14.0',   
    "category":'Odex25-Sales/Odex25-Sales',
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',  
    "depends": ['odex25_global_discount', 'sale_partner_type'],
    "data": [
        'security/security.xml',
        'views/res_partner.xml',
        'views/res_config.xml',
        'views/sale_order.xml',
    ],
  
    "sequence": 3,
    "application": False,
    "installable": True,
    "auto_install": False,

}