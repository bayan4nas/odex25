# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Membership Management, Membership subscription Plans',
    'version': '15.0.1.0',
    'sequence': 1,
    'category': 'Odex25-Sales/Odex25-Sales',
    'description':
        """
        This Module add below functionality into odoo

        1.Membership Management, Membership subscription Plans\n
        
        odoo application you can easily manage Membership. Define various membership products, create members and create their membership.

Manage membership inside the odoo
 Create and manage members
 Create Membership Product, you can decide the period of membership here it may be N number of Days, Months or Years
 Create Membership for the member, select membership product there and duration of membership will be automatically loaded based on membership product
 Create Invoice for the membership
 You can activate membership only when invoice is paid
 Membership will be automatically expire on its expiry date
 Once membership is expired you can Renew membership from there
 Separate menus provided for Active and Expire membership
 Send membership into the email to the Member
 Print membership as PDF Report
 Configure membership expiry before days so it will send notification email to the member before N number of days of expiry date of membership
 Role of Users:

    Membership > User
    Membership > Manager

        Membership Plans
Member Onboarding
Subscription Management
Renewal Notifications
Member Database
Access Control
Billing and Invoicing
Automated Renewals
Membership Tiers
Member Benefits
Membership Analytics
Member Engagement
Attendance Tracking
Event Management
Payment Gateway Integration
Custom Membership Fields
Membership Expiry Alerts
Reporting and Analytics
Membership Fees
Membership Cancellation Process

odoo app manage Membership subscription plans, odoo membership memeber, odoo member list, subscription renew, membership renew, member engagement, member expiry, membership recuring plans, membership billing, subscription expiry, subscription tracking, subscription methods and fees, membership list

    """,
    'summary': 'odoo app manage Membership subscription plans, odoo membership memeber, odoo member list, subscription renew, membership renew, member engagement, member expiry, membership recuring plans, membership billing, subscription expiry, subscription tracking, subscription methods and fees, membership list',
    'depends': ['sale_management','survey','partner_custom'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/main_menu.xml',
        'views/membership_cancel_request.xml',
        'wizard/renew_membership.xml',
        'wizard/cancel_membership.xml',
        'views/partner_extended.xml',
        'views/dev_membership.xml',
        'views/product_template.xml',
        'views/res_config_settings.xml',
        'views/membership_level.xml',
        'report/print_membership_template.xml',
        'report/print_membership_menu.xml',
        'data/mail_template.xml',
    #
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':39.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
    'license':'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
