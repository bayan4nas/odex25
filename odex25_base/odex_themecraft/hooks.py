import base64

from odoo import api, SUPERUSER_ID, _
from odoo.modules import get_module_resource
from odoo.exceptions import UserError
import os

backend_theme_attrs = {
    '$navbar_bg_color': 'rgba(31,91,117,1)',
    '$navbar_toggle': 'rgba(0,0,0,1)',
    '$selection_app_color': 'rgba(255,255,255,1)',
    '$selection_app_bg_hover': 'rgba(31,91,87,1)',
    '$navbar_ul_color': 'rgba(255,255,255,1)',
    '$navbar_ul_bg_color_hover': 'rgba(31,91,87,1)',
    '$navbar_ul_dropdown_bg_color': 'rgba(255,255,255,1)',
    '$navbar_ul_dropdown_item_color': 'rgba(31,91,117,1)',
    '$navbar_ul_dropdown_item_bg_color': 'rgba(255,255,255,1)',
    '$navbar_ul_dropdown_item_color_hover': 'rgba(255,255,255,1)',
    '$navbar_ul_dropdown_item_hover_color': 'rgba(31,91,117,1)',
    '$navbar_badge_color': 'rgba(0,0,0,1)',
    
    '$apps_bg_img': 'url(../img/odex_bg.jpg)',
    '$app_name_color': 'rgba(255,255,255,1)',
    '$app_hover_bg_color': 'rgba(31,91,87,1)',
    
    '$apps_more_info': 'rgba(31,91,117,1)',
    '$apps_install_color': 'rgba(255,255,255,1)',
    '$apps_install_bg_color': 'rgba(38,133,127,1)',
    '$apps_upgrade_color': 'rgba(255,255,255,1)',
    '$apps_upgrade_bg_color': 'rgba(31,91,117,1)',
    
    '$sections_titles_color': 'rgba(255,255,255,1)',
    '$sections_titles_bg': 'rgba(31,91,117,1)',
    
    '$filter_icon_bg_color': 'rgba(31,91,117,1)',
    '$sidebar_categories_icon_color': 'rgba(31,91,117,1)',
    '$sidebar_categories_item_color': 'rgba(0,0,0,1)',
    '$sidebar_categories_item_bg_color': 'rgba(0,0,0,1)',
    '$sidebar_categories_item_hover_active_color': 'rgba(255,255,255,1)',
    '$sidebar_categories_item_bg_hover_active_color': 'rgba(38,133,127,1)',
    
    '$english_default_font' : '"Roboto", "Odoo Unicode Support Noto", sans-serif',
    '$arabic_default_font' : '"Roboto", "Odoo Unicode Support Noto", sans-serif' 
}

def replace_file(file_path, static_dict):
        try:
            with open(file_path, 'w+') as new_file:
                for key, value in static_dict.items():
                    line = ''.join([key, ': ', value, ';\n'])
                    new_file.write(line)
            new_file.close()
        except Exception as e:
            raise UserError(_("Please follow the readme file. Contact to Administrator.""\n %s") % e)
        
def test_pre_init_hook(cr):
    """Hooks for Changing Menu Web_icon"""
    
    try:
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        theme_path = path + "/odex_themecraft/static/src/scss/variables.scss"
    except Exception as e:
        raise UserError(_("Please Contact to Administrator. \n %s") % e)
    
    replace_file(theme_path, backend_theme_attrs)
