from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'project.task'

    task_longitude = fields.Float(
        string='Customer Longitude', digits=(16, 5)
    )
    task_latitude = fields.Float(
        string='Customer Latitude', digits=(16, 5)
    )
    street = fields.Char('Street', readonly=False, store=True)
    street2 = fields.Char('Street2', readonly=False, store=True)
    zip = fields.Char('Zip', change_default=True, readonly=False, store=True)
    city = fields.Char('City', readonly=False, store=True)
    state_id = fields.Many2one(
        "res.country.state", string='State',
        readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(
        'res.country', string='Country',
        readonly=False, store=True)

    @api.model
    def _geo_localize(self, street='', zip='', city='', state='', country=''):
        geo_obj = self.env['base.geocoder']
        search = geo_obj.geo_query_address(
            street=street, zip=zip, city=city, state=state, country=country
        )
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(
                city=city, state=state, country=country
            )
            result = geo_obj.geo_find(search, force_country=country)
        return result

    def geo_localize(self):
        for task in self.with_context(lang='en_US'):
            result = self._geo_localize(
                street=task.street,
                zip=task.zip,
                city=task.city,
                state=task.state_id.name,
                country=task.country_id.name,
            )

            if result:
                task.write(
                    {
                        'task_latitude': result[0],
                        'task_longitude': result[1],
                    }
                )

        return True
