import base64
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo import modules
from odoo.exceptions import UserError
import os

def get_default_img():
    with open(modules.get_module_resource('odex_themecraft', 'static/src/img', 'app_drawer.jpeg'),'rb') as f:
        return base64.b64encode(f.read())
    
class ResIconsConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    #Icons settings
    setting_icon = fields.Binary(string="Settings Icon", attachment=True)
    apps_icon = fields.Binary(string="Apps Icon", attachment=True)
    discuss_icon = fields.Binary(string="Discuss Icon", attachment=True)
    website_icon = fields.Binary(string="Website Icon", attachment=True)
    sales_icon = fields.Binary(string="Sales Icon", attachment=True)
    invoicing_icon = fields.Binary(string="Invoicing Icon", attachment=True)
    crm_icon = fields.Binary(string="CRM Icon", attachment=True)
    mrp_icon = fields.Binary(string="MRP II Icon", attachment=True)
    inventory_icon = fields.Binary(string="Inventory Icon", attachment=True)
    accounting_icon = fields.Binary(string="Accounting Icon", attachment=True)
    purchase_icon = fields.Binary(string="Purchase Icon", attachment=True)
    pos_icon = fields.Binary(string="Point of Sale Icon", attachment=True)
    project_icon = fields.Binary(string="Project Icon", attachment=True)
    ecommerce_icon = fields.Binary(string="eCommerce Icon", attachment=True)
    manufacturing_icon = fields.Binary(string="Manufacturing Icon", attachment=True)
    email_marketing_icon = fields.Binary(string="Email Marketing Icon", attachment=True)
    timesheet_icon = fields.Binary(string="Timesheets Icon", attachment=True)
    expenses_icon = fields.Binary(string="Expenses Icon", attachment=True)
    studio_icon = fields.Binary(string="Studio Icon", attachment=True)
    time_off_icon = fields.Binary(string="Time Off Icon", attachment=True)
    recruitment_icon = fields.Binary(string="Recruitment Icon", attachment=True)
    employee_icon = fields.Binary(string="Employees Icon", attachment=True)
    maintenance_icon = fields.Binary(string="Maintenance Icon", attachment=True)
    sign_icon = fields.Binary(string="Sign Icon", attachment=True)
    helpdesk_icon = fields.Binary(string="Helpdesk Icon", attachment=True)
    subscriptions_icon = fields.Binary(string="Subscriptions Icon", attachment=True)
    quality_icon = fields.Binary(string="Quality Icon", attachment=True)
    elearning_icon = fields.Binary(string="eLearning Icon", attachment=True)
    planning_icon = fields.Binary(string="Planning Icon", attachment=True)
    data_cleaning_icon = fields.Binary(string="Data Cleaning Icon", attachment=True)
    events_icon = fields.Binary(string="Events Icon", attachment=True)
    contacts_icon = fields.Binary(string="Contacts Icon", attachment=True)
    mrp_icon = fields.Binary(string="Product Lifecycle Management (PLM) Icon", attachment=True)
    calendar_icon = fields.Binary(string="Calendar Icon", attachment=True)
    appraisal_icon = fields.Binary(string="Appraisal Icon", attachment=True)
    fleet_icon = fields.Binary(string="Fleet Icon", attachment=True)
    marketing_automation_icon = fields.Binary(string="Marketing Automation Icon", attachment=True)
    blogs_icon = fields.Binary(string="Blogs Icon", attachment=True)
    live_chat_icon = fields.Binary(string="Live Chat Icon", attachment=True)
    appointments_icon = fields.Binary(string="Appointments Icon", attachment=True)
    surveys_icon = fields.Binary(string="Surveys Icon", attachment=True)
    android_iphone_icon = fields.Binary(string="Android & iPhone Icon", attachment=True)
    dashboards_icon = fields.Binary(string="Dashboards Icon", attachment=True)
    repairs_icon = fields.Binary(string="Repairs Icon", attachment=True)
    attendance_icon = fields.Binary(string="Attendances Icon", attachment=True)
    sms_marketing_icon = fields.Binary(string="SMS Marketing Icon", attachment=True)
    barcode_icon = fields.Binary(string="Barcode Icon", attachment=True)
    notes_icon = fields.Binary(string="Notes Icon", attachment=True)
    forum_icon = fields.Binary(string="Forum Icon", attachment=True)
    skills_management_icon = fields.Binary(string="Skills Management Icon", attachment=True)
    voip_icon = fields.Binary(string="VoIP Icon", attachment=True)
    lunch_icon = fields.Binary(string="Lunch Icon", attachment=True)
    online_jobs_icon = fields.Binary(string="Online Jobs Icon", attachment=True)
    members_icon = fields.Binary(string="Members Icon", attachment=True)
    products_icon = fields.Binary(string="Products & Pricelists Icon", attachment=True)
    
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
        res = super(ResIconsConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        
        #Icons settings
        setting_icon = ir_config.get_param('setting_icon')
        apps_icon = ir_config.get_param('apps_icon')
        discuss_icon = ir_config.get_param('discuss_icon')
        website_icon = ir_config.get_param('website_icon')
        sales_icon = ir_config.get_param('sales_icon')
        invoicing_icon = ir_config.get_param('invoicing_icon')
        crm_icon = ir_config.get_param('crm_icon')
        mrp_icon = ir_config.get_param('mrp_icon')
        inventory_icon = ir_config.get_param('inventory_icon')
        accounting_icon = ir_config.get_param('accounting_icon')
        purchase_icon = ir_config.get_param('purchase_icon')
        pos_icon = ir_config.get_param('pos_icon')
        project_icon = ir_config.get_param('project_icon')
        ecommerce_icon = ir_config.get_param('ecommerce_icon')
        manufacturing_icon = ir_config.get_param('manufacturing_icon')
        email_marketing_icon = ir_config.get_param('email_marketing_icon')
        timesheet_icon = ir_config.get_param('timesheet_icon')
        expenses_icon = ir_config.get_param('expenses_icon')
        studio_icon = ir_config.get_param('studio_icon')
        time_off_icon = ir_config.get_param('time_off_icon')
        recruitment_icon = ir_config.get_param('recruitment_icon')
        employee_icon = ir_config.get_param('employee_icon')
        maintenance_icon = ir_config.get_param('maintenance_icon')
        sign_icon = ir_config.get_param('sign_icon')
        helpdesk_icon = ir_config.get_param('helpdesk_icon')
        subscriptions_icon = ir_config.get_param('subscriptions_icon')
        quality_icon = ir_config.get_param('quality_icon')
        elearning_icon = ir_config.get_param('elearning_icon')
        planning_icon = ir_config.get_param('planning_icon')
        data_cleaning_icon = ir_config.get_param('data_cleaning_icon')
        events_icon = ir_config.get_param('events_icon')
        contacts_icon = ir_config.get_param('contacts_icon')
        mrp_icon = ir_config.get_param('mrp_icon')
        calendar_icon = ir_config.get_param('calendar_icon')
        appraisal_icon = ir_config.get_param('appraisal_icon')
        fleet_icon = ir_config.get_param('fleet_icon')
        marketing_automation_icon = ir_config.get_param('marketing_automation_icon')
        blogs_icon = ir_config.get_param('blogs_icon')
        live_chat_icon = ir_config.get_param('live_chat_icon')
        appointments_icon = ir_config.get_param('appointments_icon')
        surveys_icon = ir_config.get_param('surveys_icon')
        android_iphone_icon = ir_config.get_param('android_iphone_icon')
        dashboards_icon = ir_config.get_param('dashboards_icon')
        repairs_icon = ir_config.get_param('repairs_icon')
        attendance_icon = ir_config.get_param('attendance_icon')
        sms_marketing_icon = ir_config.get_param('sms_marketing_icon')
        barcode_icon = ir_config.get_param('barcode_icon')
        notes_icon = ir_config.get_param('notes_icon')
        forum_icon = ir_config.get_param('forum_icon')
        skills_management_icon = ir_config.get_param('skills_management_icon')
        voip_icon = ir_config.get_param('voip_icon')
        lunch_icon = ir_config.get_param('lunch_icon')
        online_jobs_icon = ir_config.get_param('online_jobs_icon')
        members_icon = ir_config.get_param('members_icon')
        products_icon = ir_config.get_param('products_icon')
        
        # update resourcess
        res.update(setting_icon=setting_icon,apps_icon=apps_icon,discuss_icon=discuss_icon,website_icon=website_icon,
                   sales_icon=sales_icon,invoicing_icon=invoicing_icon,crm_icon=crm_icon,mrp_icon=mrp_icon,
                   inventory_icon=inventory_icon,accounting_icon=accounting_icon,purchase_icon=purchase_icon,
                   pos_icon=pos_icon,project_icon=project_icon,ecommerce_icon=ecommerce_icon,manufacturing_icon=manufacturing_icon,
                   email_marketing_icon=email_marketing_icon,timesheet_icon=timesheet_icon,expenses_icon=expenses_icon,
                   studio_icon=studio_icon,time_off_icon=time_off_icon,recruitment_icon=recruitment_icon,employee_icon=employee_icon,
                   maintenance_icon=maintenance_icon,sign_icon=sign_icon,helpdesk_icon=helpdesk_icon,subscriptions_icon=subscriptions_icon,
                   quality_icon=quality_icon,elearning_icon=elearning_icon,planning_icon=planning_icon,data_cleaning_icon=data_cleaning_icon,
                   events_icon=events_icon,contacts_icon=contacts_icon,calendar_icon=calendar_icon,appraisal_icon=appraisal_icon,
                   fleet_icon=fleet_icon,marketing_automation_icon=marketing_automation_icon,blogs_icon=blogs_icon,
                   live_chat_icon=live_chat_icon,appointments_icon=appointments_icon,surveys_icon=surveys_icon,android_iphone_icon=android_iphone_icon,
                   dashboards_icon=dashboards_icon,repairs_icon=repairs_icon,attendance_icon=attendance_icon,sms_marketing_icon=sms_marketing_icon,
                   barcode_icon=barcode_icon,notes_icon=notes_icon,forum_icon=forum_icon,skills_management_icon=skills_management_icon,
                   voip_icon=voip_icon,lunch_icon=lunch_icon,online_jobs_icon=online_jobs_icon,members_icon=members_icon,
                   products_icon=products_icon)
        
        return res

    def set_values(self):
        super(ResIconsConfigSettings, self).set_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        
        #Icons Settings 
        if self.setting_icon:
            menu_item = self.env['ir.ui.menu'].search([('parent_id', '=', False)])
            for menu in menu_item:
                print("***************************",menu.read())
                if menu.name == 'Settings':
                    if self.setting_icon:
                        ir_config.set_param("setting_icon",self.setting_icon)
                        menu.write({'web_icon_data': self.setting_icon})
                elif menu.name == 'Apps':
                    if self.apps_icon:
                        ir_config.set_param("apps_icon",self.apps_icon)
                        menu.write({'web_icon_data': self.apps_icon})
                elif menu.name == 'Discuss':
                    if self.discuss_icon:
                        ir_config.set_param("discuss_icon",self.discuss_icon)
                        menu.write({'web_icon_data': self.discuss_icon})
                elif menu.name == 'Website':
                    if self.website_icon:
                        ir_config.set_param("website_icon",self.website_icon)
                        menu.write({'web_icon_data': self.website_icon})
                elif menu.name == 'Sales':
                    if self.sales_icon:
                        ir_config.set_param("sales_icon",self.sales_icon)
                        menu.write({'web_icon_data': self.sales_icon})
                elif menu.name == 'Invoicing':
                    if self.invoicing_icon:
                        ir_config.set_param("invoicing_icon",self.invoicing_icon)
                        menu.write({'web_icon_data': self.invoicing_icon})
                elif menu.name == 'CRM':
                    if self.crm_icon:
                        ir_config.set_param("crm_icon",self.crm_icon)
                        menu.write({'web_icon_data': self.crm_icon})
                elif menu.name == 'MRP II':
                    if self.mrp_icon:
                        ir_config.set_param("mrp_icon",self.mrp_icon)
                        menu.write({'web_icon_data': self.mrp_icon})
                elif menu.name == 'Inventory':
                    if self.inventory_icon:
                        ir_config.set_param("inventory_icon",self.inventory_icon)
                        menu.write({'web_icon_data': self.inventory_icon})
                elif menu.name == 'Accounting':
                    if self.accounting_icon:
                        ir_config.set_param("accounting_icon",self.accounting_icon)
                        menu.write({'web_icon_data': self.accounting_icon})
                elif menu.name == 'Purchase':
                    if self.purchase_icon:
                        ir_config.set_param("purchase_icon",self.purchase_icon)
                        menu.write({'web_icon_data': self.purchase_icon})
                elif menu.name == 'Point of Sale':
                    if self.pos_icon:
                        ir_config.set_param("pos_icon",self.pos_icon)
                        menu.write({'web_icon_data': self.pos_icon})
                elif menu.name == 'Project':
                    if self.project_icon:
                        ir_config.set_param("project_icon",self.project_icon)
                        menu.write({'web_icon_data': self.project_icon})
                elif menu.name == 'eCommerce':
                    if self.ecommerce_icon:
                        ir_config.set_param("ecommerce_icon",self.ecommerce_icon)
                        menu.write({'web_icon_data': self.ecommerce_icon})
                elif menu.name == 'Manufacturing':
                    if self.manufacturing_icon:
                        ir_config.set_param("manufacturing_icon",self.manufacturing_icon)
                        menu.write({'web_icon_data': self.manufacturing_icon})
                elif menu.name == 'Email Marketing':
                    if self.email_marketing_icon:
                        ir_config.set_param("email_marketing_icon",self.email_marketing_icon)
                        menu.write({'web_icon_data': self.email_marketing_icon})
                elif menu.name == 'Timesheets':
                    if self.timesheet_icon:
                        ir_config.set_param("timesheet_icon",self.timesheet_icon)
                        menu.write({'web_icon_data': self.timesheet_icon})
                elif menu.name == 'Expenses':
                    if self.expenses_icon:
                        ir_config.set_param("expenses_icon",self.expenses_icon)
                        menu.write({'web_icon_data': self.expenses_icon})
                elif menu.name == 'Studio':
                    if self.studio_icon:
                        ir_config.set_param("studio_icon",self.studio_icon)
                        menu.write({'web_icon_data': self.studio_icon})
                elif menu.name == 'Time Off':
                    if self.time_off_icon:
                        ir_config.set_param("time_off_icon",self.time_off_icon)
                        menu.write({'web_icon_data': self.time_off_icon})
                elif menu.name == 'Recruitment':
                    if self.recruitment_icon:
                        ir_config.set_param("recruitment_icon",self.recruitment_icon)
                        menu.write({'web_icon_data': self.recruitment_icon})
                elif menu.name == 'Employees':
                    if self.employee_icon:
                        ir_config.set_param("employee_icon",self.employee_icon)
                        menu.write({'web_icon_data': self.employee_icon})
                elif menu.name == 'Maintenance':
                    if self.maintenance_icon:
                        ir_config.set_param("maintenance_icon",self.maintenance_icon)
                        menu.write({'web_icon_data': self.maintenance_icon})
                elif menu.name == 'Sign':
                    if self.sign_icon:
                        ir_config.set_param("sign_icon",self.sign_icon)
                        menu.write({'web_icon_data': self.sign_icon})
                elif menu.name == 'Helpdesk':
                    if self.helpdesk_icon:
                        ir_config.set_param("helpdesk_icon",self.helpdesk_icon)
                        menu.write({'web_icon_data': self.helpdesk_icon})
                elif menu.name == 'Subscriptions':
                    if self.subscriptions_icon:
                        ir_config.set_param("subscriptions_icon",self.subscriptions_icon)
                        menu.write({'web_icon_data': self.subscriptions_icon})
                elif menu.name == 'Quality':
                    if self.quality_icon:
                        ir_config.set_param("quality_icon",self.quality_icon)
                        menu.write({'web_icon_data': self.quality_icon})
                elif menu.name == 'eLearning':
                    if self.elearning_icon:
                        ir_config.set_param("elearning_icon",self.elearning_icon)
                        menu.write({'web_icon_data': self.elearning_icon})
                elif menu.name == 'Planning':
                    if self.planning_iconss:
                        ir_config.set_param("planning_icon",self.planning_icon)
                        menu.write({'web_icon_data': self.planning_icon})
                elif menu.name == 'Data Cleaning':
                    if self.data_cleaning_icon:
                        ir_config.set_param("data_cleaning_icon",self.data_cleaning_icon)
                        menu.write({'web_icon_data': self.data_cleaning_icon})
                elif menu.name == 'Events':
                    if self.events_icon:
                        ir_config.set_param("events_icon",self.events_icon)
                        menu.write({'web_icon_data': self.events_icon})
                elif menu.name == 'Contacts':
                    if self.contacts_icon:
                        ir_config.set_param("contacts_icon",self.contacts_icon)
                        menu.write({'web_icon_data': self.contacts_icon})
                elif menu.name == 'Product Lifecycle Management (PLM)':
                    if self.mrp_icon:
                        ir_config.set_param("mrp_icon",self.mrp_icon)
                        menu.write({'web_icon_data': self.mrp_icon})
                elif menu.name == 'Calendar':
                    if self.calendar_icon:
                        ir_config.set_param("calendar_icon",self.calendar_icon)
                        menu.write({'web_icon_data': self.calendar_icon})
                elif menu.name == 'Appraisal':
                    if self.appraisal_icon:
                        ir_config.set_param("appraisal_icon",self.appraisal_icon)
                        menu.write({'web_icon_data': self.appraisal_icon})
                elif menu.name == 'Fleet':
                    if self.fleet_icon:
                        ir_config.set_param("fleet_icon",self.fleet_icon)
                        menu.write({'web_icon_data': self.fleet_icon})
                elif menu.name == 'Marketing Automation':
                    if self.marketing_automation_icon:
                        ir_config.set_param("marketing_automation_icon",self.marketing_automation_icon)
                        menu.write({'web_icon_data': self.marketing_automation_icon})
                elif menu.name == 'Blogs':
                    if self.blogs_icon:
                        ir_config.set_param("blogs_icon",self.blogs_icon)
                        menu.write({'web_icon_data': self.blogs_icon})
                elif menu.name == 'Live Chat':
                    if self.live_chat_icon:
                        ir_config.set_param("live_chat_icon",self.live_chat_icon)
                        menu.write({'web_icon_data': self.live_chat_icon})
                elif menu.name == 'Appointments':
                    if self.appointments_icon:
                        ir_config.set_param("appointments_icon",self.appointments_icon)
                        menu.write({'web_icon_data': self.appointments_icon})
                elif menu.name == 'Surveys':
                    if self.surveys_icon:
                        ir_config.set_param("surveys_icon",self.surveys_icon)
                        menu.write({'web_icon_data': self.surveys_icon})
                elif menu.name == 'Android & iPhone':
                    if self.android_iphone_icon:
                        ir_config.set_param("android_iphone_icon",self.android_iphone_icon)
                        menu.write({'web_icon_data': self.android_iphone_icon})
                elif menu.name == 'Dashboards':
                    if self.dashboards_icon:
                        ir_config.set_param("dashboards_icon",self.dashboards_icon)
                        menu.write({'web_icon_data': self.dashboards_icon})
                elif menu.name == 'Repairs':
                    if self.repairs_icon:
                        ir_config.set_param("repairs_icon",self.repairs_icon)
                        menu.write({'web_icon_data': self.repairs_icon})
                elif menu.name == 'Attendances':
                    if self.attendance_icon:
                        ir_config.set_param("attendance_icon",self.attendance_icon)
                        menu.write({'web_icon_data': self.attendance_icon})
                elif menu.name == 'SMS Marketing':
                    if self.sms_marketing_icon:
                        ir_config.set_param("sms_marketing_icon",self.sms_marketing_icon)
                        menu.write({'web_icon_data': self.sms_marketing_icon})
                elif menu.name == 'Barcode':
                    if self.barcode_icon:
                        ir_config.set_param("barcode_icon",self.barcode_icon)
                        menu.write({'web_icon_data': self.barcode_icon})
                elif menu.name == 'Notes':
                    if self.notes_icon:
                        ir_config.set_param("notes_icon",self.notes_icon)
                        menu.write({'web_icon_data': self.notes_icon})
                elif menu.name == 'Forum':
                    if self.forum_icon:
                        ir_config.set_param("forum_icon",self.forum_icon)
                        menu.write({'web_icon_data': self.forum_icon})
                elif menu.name == 'Skills Management':
                    if self.skills_management_icon:
                        ir_config.set_param("skills_management_icon",self.skills_management_icon)
                        menu.write({'web_icon_data': self.skills_management_icon})
                elif menu.name == 'VoIP':
                    if self.voip_icon:
                        ir_config.set_param("voip_icon",self.voip_icon)
                        menu.write({'web_icon_data': self.voip_icon})
                elif menu.name == 'Lunch':
                    if self.lunch_icon:
                        ir_config.set_param("lunch_icon",self.lunch_icon)
                        menu.write({'web_icon_data': self.lunch_icon})
                elif menu.name == 'Online Jobs':
                    if self.online_jobs_icon:
                        ir_config.set_param("online_jobs_icon",self.online_jobs_icon)
                        menu.write({'web_icon_data': self.online_jobs_icon})
                elif menu.name == 'Members':
                    if self.members_icon:
                        ir_config.set_param("members_icon",self.members_icon)
                        menu.write({'web_icon_data': self.members_icon})
                elif menu.name == 'Products & Pricelists':
                    if self.products_icon:
                        ir_config.set_param("products_icon",self.products_icon)
                        menu.write({'web_icon_data': self.products_icon})
        