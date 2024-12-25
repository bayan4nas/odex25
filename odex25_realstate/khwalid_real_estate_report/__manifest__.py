# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################


{
    'name': 'Khwalid Real Estate Report',
    'version': '1.0',
    'license': 'AGPL-3',
    'category': 'Odex25-Realstate/Odex25-Realstate',
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'summary': "Khwalid Real Estate Report ",
    'depends': ['khawald_real_estate_marketing', 'report_xlsx'],
    'data': [
        'reports/property_reservation_cheque_report_template.xml',
        'reports/receipt_voucher_report_template.xml',
        'reports/refund_request_report_template.xml',
        'reports/customer_Identi_without_image_report_template.xml',
        'reports/receive_unit_report_template.xml',
        'reports/report_invoice.xml',
        'reports/permission_empty_unit_report_template.xml',
    ],
    
    'installable': True,
    'application': False,
}