# -*- coding: utf-8 -*-
##############################################################################
#
#    (Odex - Extending the base module).
#    Copyright (C) 2024 Expert Co. Ltd. (<http://exp-sa.com>).
#
##############################################################################
{
    "name": "Odex -KPI",
    "version": "1.0",
    "author": "Expert Co. Ltd.",
    "category": "Odex25-base/Odex-Base25",
    "website": "http://www.exp-sa.com",
    "installable": True,
    "depends": [
        "kpi_scorecard",
        
    ],
    "data": [
       "security/ir.model.access.csv",
        "views/kpi_category.xml",
        "views/kpi_item.xml",
        "views/kpi_scorecard_line.xml",
        'views/menu_security_cus.xml'
        
        
        
        
        
        
    ],
    
    

}
