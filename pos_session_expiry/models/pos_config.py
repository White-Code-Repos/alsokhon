""" init object pos.config """

from odoo import fields, models


class PosConfig(models.Model):
    """ init object pos.config """
    _inherit = 'pos.config'

    session_expiry_seconds = fields.Integer(
        help="The number of idle seconds required to end the session.",
    )
