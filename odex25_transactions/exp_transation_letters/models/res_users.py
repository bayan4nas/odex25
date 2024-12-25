from odoo import models,fields, api, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    letter_id = fields.Many2one('letters.letters')
    attachment_id = fields.Many2one('cm.attachment.rule')

    def write(self, vals):
        # Access the context
        context = self.env.context

        # Retrieve the letter_id from the context
        letter_id = context.get('default_letter_id') if context else None
        attachment_id = context.get('default_attachment_id') if context else None

        # Custom logic before updating the record
        if letter_id:
            # Ensure letter_id is a valid recordset
            letter_record = self.env['letters.letters'].browse(letter_id)
            if letter_record.exists():
                letter_record.new_signature = vals.get('sign_signature') if vals.get('sign_signature') else self.env.user.sign_signature
                letter_record.action_generate_attachment()
        if attachment_id:
            attachment_record = self.env['cm.attachment.rule'].browse(attachment_id)
            if attachment_record:
                attachment_record.signed = True


        # Call the super method to perform the standard write operation
        result = super(ResUsers, self).write(vals)

        return result