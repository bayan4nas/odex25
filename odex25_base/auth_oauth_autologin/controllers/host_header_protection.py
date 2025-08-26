from odoo import models, http, tools
from werkzeug.exceptions import BadRequest

#  - 1.3.12 : Redirection Through Header Injection


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls):
        # Hardcoded allowed hosts (case-insensitive)
        allowed_hosts = {
            'testerp.saip.gov.sa',
            'localhost:8080',
            'stgerp.saip.gov.sa',
            'erp.saip.gov.sa',
            'saipersgate.saip.gov.sa'
        }
        allowed_hosts = {h.strip().lower() for h in allowed_hosts if h.strip()}

        if allowed_hosts:
            # Validate Host header (with port if specified)
            incoming_host = http.request.httprequest.host.lower()
            if incoming_host not in allowed_hosts:
                raise BadRequest(f"Invalid Host header: {incoming_host}")

            # Validate risky headers (e.g., X-Forwarded-Host)
            headers_to_check = [
                'X-Forwarded-Host',
                'X-Host',
                'X-Forward-Server'
            ]
            for header in headers_to_check:
                header_value = http.request.httprequest.headers.get(header)
                if header_value:
                    # Split comma-separated values
                    hosts = [h.strip().lower() for h in header_value.split(',')]
                    for host in hosts:
                        if host not in allowed_hosts:
                            raise BadRequest(f"Invalid {header} header: {host}")

        # Call the original _dispatch method
        return super(IrHttp, cls)._dispatch()