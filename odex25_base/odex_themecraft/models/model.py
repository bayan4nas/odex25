import base64
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo import modules
from odoo.exceptions import UserError
from odoo.modules import get_module_resource
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

def get_default_img():
    with open(modules.get_module_resource('odex_themecraft', 'static/src/img', 'app_drawer.jpeg'),'rb') as f:
        return base64.b64encode(f.read())
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Navigation Bar
    navbar_bg_color = fields.Char(string='Navbar Background',default="rgba(31,91,117,1)")
    navbar_toggle = fields.Char(string='Navbar Background (Hover)',default="rgba(0,0,0,1)")
    selection_app_color = fields.Char(string='Main Menu Title Background',default="rgba(255,255,255,1)")
    selection_app_bg_hover = fields.Char(string='Main Menu Title Background (Hover)',default="rgba(31,91,87,1)")
    navbar_ul_color = fields.Char(string='Navbar Item Color',default="rgba(255,255,255,1)")
    navbar_ul_bg_color_hover = fields.Char(string='Navbar Item Background (Hover)',default="rgba(31,91,87,1)")
    navbar_ul_dropdown_bg_color = fields.Char(string='Navbar Dropdown Background',default="rgba(255,255,255,1)")
    navbar_ul_dropdown_item_color = fields.Char(string='Navbar Dropdown Item Color',default="rgba(31,91,117,1)")
    navbar_ul_dropdown_item_color_hover = fields.Char(string='Navbar Dropdown Color (Hover)',default="rgba(255,255,255,1)")
    navbar_ul_dropdown_item_bg_color = fields.Char(string='Navbar Dropdown Item Background',default="rgba(255,255,255,1)")
    navbar_ul_dropdown_item_hover_color = fields.Char(string='Navbar Dropdown Item Background (Hover)',default="rgba(31,91,117,1)")
    navbar_badge_color = fields.Char(string='Navbar Counter Badge Background',default="rgba(0,0,0,1)")
    # App Drawer (home)
    apps_bg_img = fields.Binary(string="App Drawer Background", attachment=True,default=get_default_img())
    app_name_color = fields.Char(string='Navbar Counter Badge Background',default="rgba(255,255,255,1)")
    app_hover_bg_color = fields.Char(string='App Background (Hover)',default="rgba(31,91,87,1)")
    # Apps Module
    apps_more_info = fields.Char(string='Apps More Info Button Background',default="rgba(31,91,117,1)")
    apps_install_color = fields.Char(string='Apps Install Button Color',default="rgba(255,255,255,1)")
    apps_install_bg_color = fields.Char(string='Apps Install Button Background',default="rgba(31,91,117,1)")
    apps_upgrade_color = fields.Char(string='Apps Upgrade Button Color',default="rgba(255,255,255,1)")
    apps_upgrade_bg_color = fields.Char(string='Apps Upgrade Button Background',default="rgba(31,91,117,1)")
    # Setting Module
    sections_titles_color = fields.Char(string='Section Titles Color',default="rgba(255,255,255,1)")
    sections_titles_bg = fields.Char(string='Section Titles Background',default="rgba(31,91,117,1)")
    # Font Settings
    english_default_font = fields.Selection([
        ('default','Default'),
        ('font_1','Helvetica'),
        ('font_2','Futura'),
        ('font_3','Garamond'),
        ('font_4','Times'),
        ('font_5','Arial'),
        ('font_6','Verdana'),
        ('font_7','Comic Sans'),
        ('font_8','Trebuchet'),
        ('font_9','Gill Sans'),
        ('font_10','Georgia'),
    ], string='English Default Font', config_parameter='odex_themecraft.english_default_font', default='default')
    arabic_default_font = fields.Selection([
        ('default','Default'),
        ('font_1','Arial'),
        ('font_2','Droid Kufi'),
        ('font_3','Aniri'),
        ('font_4','Droid Naskh'),
        ('font_5','Frutiger LT Arabic'),
    ], string='Arabic Default Font', config_parameter='odex_themecraft.arabic_default_font', default='default')
    #Icons settings
    setting_icon = fields.Binary(string="Settings Icon", attachment=True)
    
    def replace_file(self, file_path, static_dict):
        try:
            with open(file_path, 'w+') as new_file:
                for key, value in static_dict.items():
                    line = ''.join([key, ': ', value, ';\n'])
                    new_file.write(line)
            new_file.close()
        except Exception as e:
            raise UserError(_("Please follow the readme file. Contact to Administrator.""\n %s") % e)
            
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        
        # Navigation Bar
        navbar_bg_color = ir_config.get_param('navbar_bg_color',"rgba(31,91,117,1)")
        navbar_toggle = ir_config.get_param('navbar_toggle',"rgba(0,0,0,1)")
        selection_app_color = ir_config.get_param('selection_app_color',"rgba(255,255,255,1)")
        selection_app_bg_hover = ir_config.get_param('selection_app_bg_hover',"rgba(31,91,87,1)")
        navbar_ul_color = ir_config.get_param('navbar_ul_color',"rgba(31,91,87,1)")
        navbar_ul_bg_color_hover = ir_config.get_param('navbar_ul_bg_color_hover',"rgba(255,255,255,1)")
        navbar_ul_dropdown_bg_color = ir_config.get_param('navbar_ul_dropdown_bg_color',"rgba(31,91,117,1)")
        navbar_ul_dropdown_item_color = ir_config.get_param('navbar_ul_dropdown_item_color',"rgba(31,91,117,1)")
        navbar_ul_dropdown_item_color_hover = ir_config.get_param('navbar_ul_dropdown_item_color_hover',"rgba(255,255,255,1)")
        navbar_ul_dropdown_item_bg_color = ir_config.get_param('navbar_ul_dropdown_item_bg_color',"rgba(255,255,255,1)")
        navbar_ul_dropdown_item_hover_color = ir_config.get_param('navbar_ul_dropdown_item_hover_color',"rgba(31,91,117,1)")
        navbar_badge_color = ir_config.get_param('navbar_badge_color',"rgba(0,0,0,1)")
        # App Drawer (home)
        apps_bg_img = ir_config.get_param('apps_bg_img')
        app_name_color = ir_config.get_param('app_name_color',"rgba(255,255,255,1)")
        app_hover_bg_color = ir_config.get_param('app_hover_bg_color',"rgba(31,91,87,1)")
        # Apps Module
        apps_more_info = ir_config.get_param('apps_more_info',"rgba(31,91,117,1)")
        apps_install_color = ir_config.get_param('apps_install_color',"rgba(255,255,255,1)")
        apps_install_bg_color = ir_config.get_param('apps_install_bg_color',"rgba(31,91,117,1)")
        apps_upgrade_color = ir_config.get_param('apps_upgrade_color',"rgba(255,255,255,1)")
        apps_upgrade_bg_color = ir_config.get_param('apps_upgrade_bg_color',"rgba(31,91,117,1)")
        # Setting Module
        sections_titles_color = ir_config.get_param('sections_titles_color',"rgba(255,255,255,1)")
        sections_titles_bg = ir_config.get_param('sections_titles_bg',"rgba(31,91,117,1)")
        # Fonts Settings 
        english_default_font = ir_config.get_param('english_default_font','default')
        arabic_default_font = ir_config.get_param('arabic_default_font','default')
        
        # update resourcess
        res.update(navbar_bg_color=navbar_bg_color,navbar_toggle=navbar_toggle,selection_app_color=selection_app_color,
                   selection_app_bg_hover=selection_app_bg_hover,navbar_ul_color=navbar_ul_color,navbar_ul_bg_color_hover=navbar_ul_bg_color_hover,
                   navbar_ul_dropdown_bg_color=navbar_ul_dropdown_bg_color,navbar_ul_dropdown_item_color=navbar_ul_dropdown_item_color,
                   navbar_ul_dropdown_item_color_hover=navbar_ul_dropdown_item_color_hover,navbar_ul_dropdown_item_bg_color=navbar_ul_dropdown_item_bg_color,
                   navbar_ul_dropdown_item_hover_color=navbar_ul_dropdown_item_hover_color,navbar_badge_color=navbar_badge_color,
                   apps_bg_img=apps_bg_img,app_name_color=app_name_color,app_hover_bg_color=app_hover_bg_color,apps_more_info=apps_more_info,
                   apps_install_color=apps_install_color,apps_install_bg_color=apps_install_bg_color,apps_upgrade_color=apps_upgrade_color,
                   apps_upgrade_bg_color=apps_upgrade_bg_color,sections_titles_color=sections_titles_color,sections_titles_bg=sections_titles_bg,
                   english_default_font=english_default_font,arabic_default_font=arabic_default_font)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        
        # Navigation Bar
        ir_config.set_param("navbar_bg_color",self.navbar_bg_color)
        ir_config.set_param("navbar_toggle",self.navbar_toggle)
        ir_config.set_param("selection_app_color",self.selection_app_color)
        ir_config.set_param("selection_app_bg_hover",self.selection_app_bg_hover)
        ir_config.set_param("navbar_ul_color",self.navbar_ul_color)
        ir_config.set_param("navbar_ul_bg_color_hover",self.navbar_ul_bg_color_hover)
        ir_config.set_param("navbar_ul_dropdown_bg_color",self.navbar_ul_dropdown_bg_color)
        ir_config.set_param("navbar_ul_dropdown_item_color",self.navbar_ul_dropdown_item_color)
        ir_config.set_param("navbar_ul_dropdown_item_color_hover",self.navbar_ul_dropdown_item_color_hover)
        ir_config.set_param("navbar_ul_dropdown_item_bg_color",self.navbar_ul_dropdown_item_bg_color)
        ir_config.set_param("navbar_ul_dropdown_item_hover_color",self.navbar_ul_dropdown_item_hover_color)
        ir_config.set_param("navbar_badge_color",self.navbar_badge_color)
        # App Drawer (home)
        ir_config.set_param("apps_bg_img",self.apps_bg_img)
        ir_config.set_param("app_name_color",self.app_name_color)
        ir_config.set_param("app_hover_bg_color",self.app_hover_bg_color)
        # Apps Module
        ir_config.set_param("apps_more_info",self.apps_more_info)
        ir_config.set_param("apps_install_color",self.apps_install_color)
        ir_config.set_param("apps_install_bg_color",self.apps_install_bg_color)
        ir_config.set_param("apps_upgrade_color",self.apps_upgrade_color)
        ir_config.set_param("apps_upgrade_bg_color",self.apps_upgrade_bg_color)
        # Setting Module
        ir_config.set_param("sections_titles_color",self.sections_titles_color)
        ir_config.set_param("sections_titles_bg",self.sections_titles_bg)
        #Font Settings
        ir_config.set_param("english_default_font",self.english_default_font)
        ir_config.set_param("arabic_default_font",self.arabic_default_font)
        #Icons settings
        ir_config.set_param("setting_icon",self.setting_icon)
        
        try:
            path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            theme_path = path + "/odex_themecraft/static/src/scss/variables.scss"
        except Exception as e:
            raise UserError(_("Please Contact to Administrator. \n %s") % e)

        # Navigation Bar
        if self.navbar_bg_color:
            backend_theme_attrs.update({'$navbar_bg_color': self.navbar_bg_color})
        if self.navbar_toggle:
            backend_theme_attrs.update({'$navbar_toggle': self.navbar_toggle})
        if self.selection_app_color:
            backend_theme_attrs.update({'$selection_app_color': self.selection_app_color})
        if self.selection_app_bg_hover:
            backend_theme_attrs.update({'$selection_app_bg_hover': self.selection_app_bg_hover})
        if self.navbar_ul_color:
            backend_theme_attrs.update({'$navbar_ul_color': self.navbar_ul_color})
        if self.navbar_ul_bg_color_hover:
            backend_theme_attrs.update({'$navbar_ul_bg_color_hover': self.navbar_ul_bg_color_hover})
        if self.navbar_ul_dropdown_bg_color:
            backend_theme_attrs.update({'$navbar_ul_dropdown_bg_color': self.navbar_ul_dropdown_bg_color})
        if self.navbar_ul_dropdown_item_color:
            backend_theme_attrs.update({'$navbar_ul_dropdown_item_color': self.navbar_ul_dropdown_item_color})
        if self.navbar_ul_dropdown_item_color_hover:
            backend_theme_attrs.update({'$navbar_ul_dropdown_item_color_hover': self.navbar_ul_dropdown_item_color_hover})
        if self.navbar_ul_dropdown_item_bg_color:
            backend_theme_attrs.update({'$navbar_ul_dropdown_item_bg_color': self.navbar_ul_dropdown_item_bg_color})
        if self.navbar_badge_color:
            backend_theme_attrs.update({'$navbar_badge_color': self.navbar_badge_color})
            
        # App Drawer (home)
        if self.apps_bg_img:
            backend_theme_attrs.update({'$apps_bg_img': "url('" + ("/web/image/res.config.settings/%s/apps_bg_img" % self.id) + "')"})         
        if self.app_name_color:
            backend_theme_attrs.update({'$app_name_color': self.app_name_color})
        if self.app_hover_bg_color:
            backend_theme_attrs.update({'$app_hover_bg_color': self.app_hover_bg_color})
        
        # Apps Module
        if self.apps_more_info:
            backend_theme_attrs.update({'$apps_more_info': self.apps_more_info})
        if self.apps_install_color:
            backend_theme_attrs.update({'$apps_install_color': self.apps_install_color})
        if self.apps_install_bg_color:
            backend_theme_attrs.update({'$apps_install_bg_color': self.apps_install_bg_color})
        if self.apps_upgrade_color:
            backend_theme_attrs.update({'$apps_upgrade_color': self.apps_upgrade_color})
        if self.apps_upgrade_bg_color:
            backend_theme_attrs.update({'$apps_upgrade_bg_color': self.apps_upgrade_bg_color})
        
        # Setting Module
        if self.sections_titles_color:
            backend_theme_attrs.update({'$sections_titles_color': self.sections_titles_color})
        if self.sections_titles_bg:
            backend_theme_attrs.update({'$sections_titles_bg': self.sections_titles_bg})
            
        # Font Settings
        # English Font
        if self.english_default_font:
            english_font = '"Roboto", "Odoo Unicode Support Noto", sans-serif'
            if self.english_default_font == 'font_1':
                english_font = 'Helvetica, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            elif self.english_default_font == 'font_2':
                english_font = 'Futura, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            elif self.english_default_font == 'font_3':
                english_font = 'Garamond, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            elif self.english_default_font == 'font_4':
                english_font = 'Times, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            elif self.english_default_font == 'font_5':
                english_font = 'Arial, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            elif self.english_default_font == 'font_6':
                english_font = 'Verdana, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            elif self.english_default_font == 'font_7':
                english_font = 'Comic Sans, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            elif self.english_default_font == 'font_8':
                english_font = 'Trebuchet, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            elif self.english_default_font == 'font_9':
                english_font = 'Gill Sans, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            elif self.english_default_font == 'font_10':
                english_font = 'Georgia, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            # Update english default font
            backend_theme_attrs.update({'$english_default_font': english_font})
        # Arabic Font   
        if self.arabic_default_font:
            arabic_font = '"Roboto", "Odoo Unicode Support Noto", sans-serif'
            if self.arabic_default_font == 'font_1':
                arabic_font = 'Arial, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            if self.arabic_default_font == 'font_2':
                arabic_font = '"Droid Arabic Kufi", "Roboto", "Odoo Unicode Support Noto", sans-serif'
            if self.arabic_default_font == 'font_3':
                arabic_font = 'Amiri, "Roboto", "Odoo Unicode Support Noto", sans-serif'
            if self.arabic_default_font == 'font_4':
                arabic_font = '"Droid Arabic Naskh", "Roboto", "Odoo Unicode Support Noto", sans-serif'
            if self.arabic_default_font == 'font_5':
                arabic_font = '"Frutiger LT Arabic", "Roboto", "Odoo Unicode Support Noto", sans-serif'
            # Update arabic default font
            backend_theme_attrs.update({'$arabic_default_font': arabic_font})
                    
        self.replace_file(theme_path, backend_theme_attrs)
        