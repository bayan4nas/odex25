{
    'name':'Maintenance Custom ',
    'version':'1.0',
    'summary':'Maintenance Custom system',
    'sequence': 1,
    'description':
    """
    """,
    'depends':['sale','purchase_requisition_custom', 'maintenance','hr_maintenance'],
    'data':[
            'security/ir.model.access.csv',
            'data/ir_sequences_data.xml',
            'security/groups.xml',
            'views/maintenance_view.xml',
            'views/maintenance_asset.xml',
            'views/maintenance_checklist.xml',
            'views/menu_security_cus.xml',
            'wizard/maintenance_report_wiz_view.xml',
            'reports/equipment_report.xml',
            'reports/spare_part_report.xml',
            'reports/general_maintenance_report.xml',
            'reports/report_maintenance_request.xml',
            'reports/maintenance_report.xml',
            'reports/maintenance_team_report.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable':
    True,
    'application':
    True,
}
