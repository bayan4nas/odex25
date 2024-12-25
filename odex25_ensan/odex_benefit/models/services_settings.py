from odoo import fields, models, api, _


class ServicesSettings(models.Model):
    _name = 'services.settings'
    _rec_name = 'service_name'

    service_name = fields.Char(string='Service Name')
    parent_service = fields.Many2one('services.settings',string='Parent Service')
    is_main_service = fields.Boolean(string='Is Main Service?')
    is_service_producer = fields.Boolean(string='Is Service Producer?')
    service_producer_id = fields.Many2one('res.partner',string='Service Producer')
    is_this_service_for_student = fields.Boolean(string='Is Service For Student?')
    service_type = fields.Selection([('rent', 'Rent'),('home_restoration', 'Home Restoration'),('alternative_housing', 'Alternative Housing'),('home_maintenance','Home Maintenance')
                                        ,('complete_building_house','Complete Building House'),('electrical_devices','Electrical Devices'),('home_furnishing','Home furnishing')
                                        ,('electricity_bill','Electricity bill'),('water_bill','Water bill'),('buy_car','Buy Car'),('recruiting_driver','Recruiting Driver')
                                        ,('transportation_insurance','Transportation Insurance'),('debits','Debits'),('health_care','Health Care'),
                                     ('providing_medicines_medical_devices_and_needs_the_disabled','Providing Medicines Medical Devices And Needs The Disabled'),
                                     ('recruiting_domestic_worker_or_nurse','Recruiting a domestic worker or nurse') ,('marriage','Marriage'),('eid_gift','Eid gift'),
                                     ('winter_clothing','Winter clothing'),('ramadan_basket','Ramadan basket'),('natural_disasters','Natural disasters'),
                                     ('legal_arguments','Legal arguments'),('buy_home','Buy Home')]
                                    ,string='Service Type')
    max_amount_for_student = fields.Float(string='Max Amount for Student')
    raise_amount_for_orphan = fields.Float(string='Raise Amount For Orphan')
    rent_lines = fields.One2many('rent.lines','services_settings_id')
    attachment_lines = fields.One2many('service.attachments.settings','service_id')
    #Fields for home restoration
    home_restoration_lines = fields.One2many('home.restoration.lines','services_settings_id')
    rent_amount_for_alternative_housing = fields.Float(string='Rent Amount For Alternative Housing')
    rent_period = fields.Integer('Rent Period')
    home_maintenance_lines = fields.One2many('home.maintenance.lines','services_settings_id')
    benefit_category_ids = fields.Many2many('benefit.category', string='Allowed Categories')
    max_maintenance_amount = fields.Float(string='Max Maintenance Amount')
    account_id = fields.Many2one('account.account',string='Expenses Account',domain="[('user_type_id.id','=',15)]")
    accountant_id = fields.Many2one('res.users',string='Accountant')
    #Fields for Complete Building House
    max_complete_building_house_amount = fields.Float(string='Max Complete Building House Amount')
    #For Electrical Devices
    electrical_devices_lines = fields.One2many('electrical.devices','services_settings_id')
    #Home Furnishing
    home_furnishing_lines = fields.One2many('home.furnishing.lines','services_settings_id')
    max_furnishing_amount = fields.Float(string='Max Furnishing Amount')
    max_furnishing_amount_if_exception = fields.Float(string='Max Furnishing Amount (Exception)')
    #Electricity Bill
    electricity_bill_lines = fields.One2many('electricity.bill.lines','services_settings_id')
    # Water Bill
    water_bill_lines = fields.One2many('water.bill.lines', 'services_settings_id')
    #Buy Car
    max_buy_car_amount = fields.Float(string='Max Buy Car Amount')
    min_count_member = fields.Integer(string='Mini Count Member')
    #Recruiting_driver
    max_recruiting_driver_amount = fields.Float(string='Max Buy Car Amount')
    #Transportation insurance
    max_government_transportation_amount = fields.Float(string='Max Government Transportation Amount')
    max_universities_training_institutes_transportation_amount = fields.Float(string='Max Universities Training Institutes Transportation Amount')
    max_hospitals_transportation_amount = fields.Float(string='Max Hospitals Transportation Amount')
    max_programs_transportation_amount = fields.Float(string='Max Programs Transportation Amount')
    #Debits
    max_debits_amount = fields.Float(string='Max Debits Amount')
    #Health_care
    max_health_care_amount = fields.Float(string='Max Health Care Amount In Year')
    #recruiting_domestic_worker_or_nurse
    max_recruiting_domestic_worker_or_nurse_amount = fields.Float(string='Max Recruiting Domestic Worker Or Nurse Care Amount')
    # Marriage
    member_max_age = fields.Integer(string='Member Max Age')
    member_max_payroll = fields.Float(string='Member Max Payroll')
    fatherless_member_amount = fields.Float(string='Fatherless Member Amount')
    orphan_member_amount = fields.Float(string='Orphan Member Amount')
    # Eid Gift
    eid_gift_max_age = fields.Integer(string='Eid Gift Max Age')
    eid_gift_member_amount = fields.Float(string='Eid Gift Member Amount')
    #Winter clothing
    winter_clothing_member_amount = fields.Float(string="Winter clothing Member Amount")
    #Ramadan Basket
    ramadan_basket_member_amount = fields.Float(string='Ramadan Basket Member Amount')
    #Natural disasters
    natural_disasters_max_amount = fields.Float(string='Natural disasters Max Amount')
    # Legal Arguments
    legal_arguments_max_amount = fields.Float(string='Legal Arguments Max Amount')
    #Buy Home
    buy_home_lines = fields.One2many('buy.home.lines', 'services_settings_id')
    buy_home_max_total_amount = fields.Float(string='Buy Home Max Total Amount')
    home_age = fields.Integer(string='Home Age')

class RentLines(models.Model):
    _name = 'rent.lines'

    benefit_category_id = fields.Many2one('benefit.category', string='Benefit Category')
    services_settings_id = fields.Many2one('services.settings', string='Services Settings')
    benefit_count = fields.Integer('Benefit Count')
    estimated_rent_branches = fields.Float(string='Estimated Rent Branches')
    estimated_rent_governorate = fields.Float(string='Estimated Rent Governorate')
    discount_rate_shared_housing = fields.Float(string='Discount Rate For Shared housing')

class HomeRestorationLines(models.Model):
    _name = 'home.restoration.lines'

    benefit_category_id = fields.Many2one('benefit.category', string='Benefit Category')
    services_settings_id = fields.Many2one('services.settings', string='Services Settings')
    max_amount = fields.Float(string='Max Amount')

class HomeMaintenanceLines(models.Model):
    _name = 'home.maintenance.lines'
    _rec_name = 'maintenance_name'

    services_settings_id = fields.Many2one('services.settings', string='Services Settings')
    maintenance_name = fields.Char(string='Maintenance Name')

class ElectricalDevices(models.Model):
    _name = 'electrical.devices'
    _rec_name = 'device_name'

    min_count_member = fields.Integer(string='From')
    max_count_member = fields.Integer(string='To')
    device_name = fields.Char(string="Device Name")
    allowed_quantity = fields.Integer(string='Allowed Quantity')
    account_id = fields.Many2one('account.account',string='Expenses Account',domain="[('user_type_id.id','=',15)]")
    services_settings_id = fields.Many2one('services.settings')

class HomeFurnishingLines(models.Model):
    _name = 'home.furnishing.lines'

    services_settings_id = fields.Many2one('services.settings')
    name = fields.Char(string="Furnishing Name")
    max_furnishing_amount = fields.Float(string='Furnishing Amount')

class ElectricityBillLines(models.Model):
    _name = 'electricity.bill.lines'

    benefit_category_id = fields.Many2one('benefit.category', string='Benefit Category')
    min_count_member = fields.Integer(string='From')
    max_count_member = fields.Integer(string='To')
    max_amount_for_electricity_bill = fields.Float(string='Max Amount For Electricity Bill')
    services_settings_id = fields.Many2one('services.settings', string='Services Settings')

class WaterBillLines(models.Model):
    _name = 'water.bill.lines'

    benefit_category_id = fields.Many2one('benefit.category', string='Benefit Category')
    min_count_member = fields.Integer(string='From')
    max_count_member = fields.Integer(string='To')
    max_amount_for_water_bill = fields.Float(string='Max Amount For Electricity Bill')
    services_settings_id = fields.Many2one('services.settings', string='Services Settings')

class BuyHomeLines(models.Model):
    _name = 'buy.home.lines'

    min_count_member = fields.Integer(string='From')
    max_count_member = fields.Integer(string='To')
    amount_for_buy_home = fields.Float(string='Amount For Buy Home')
    services_settings_id = fields.Many2one('services.settings', string='Services Settings')

