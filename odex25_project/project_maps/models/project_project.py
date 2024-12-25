from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    project_longitude = fields.Float(
        string='Customer Longitude', digits=(16, 5)
    )
    project_latitude = fields.Float(
        string='Customer Latitude', digits=(16, 5)
    )


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
        for project in self.with_context(lang='en_US'):
            result = self._geo_localize(
                street=project.street,
                zip=project.zip,
                city=project.city,
                state=project.state_id.name,
                country=project.country_id.name,
            )

            if result:
                project.write(
                    {
                        'project_latitude': result[0],
                        'project_longitude': result[1],
                    }
                )

        return True
