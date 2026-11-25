from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_maladiwa_receipt_enabled = fields.Boolean(
        related="pos_config_id.maladiwa_receipt_enabled",
        readonly=False,
    )

    pos_maladiwa_usd_rate = fields.Float(
        related="pos_config_id.maladiwa_usd_rate",
        readonly=False,
    )

    pos_maladiwa_restaurant_name = fields.Char(
        related="pos_config_id.maladiwa_restaurant_name",
        readonly=False,
    )

    pos_maladiwa_bank_mvr = fields.Char(
        related="pos_config_id.maladiwa_bank_mvr",
        readonly=False,
    )

    pos_maladiwa_bank_usd = fields.Char(
        related="pos_config_id.maladiwa_bank_usd",
        readonly=False,
    )

    pos_maladiwa_gst_tax_id = fields.Many2one(
        related="pos_config_id.maladiwa_gst_tax_id",
        readonly=False,
    )

    pos_maladiwa_service_product_id = fields.Many2one(
        related="pos_config_id.maladiwa_service_product_id",
    )

    pos_maladiwa_dine_in_preset_id = fields.Many2one(
        related="pos_config_id.maladiwa_dine_in_preset_id",
    )

    pos_maladiwa_takeaway_preset_id = fields.Many2one(
        related="pos_config_id.maladiwa_takeaway_preset_id",
    )

    def action_maladiwa_prepare(self):
        self.ensure_one()
        return self.pos_config_id.action_maladiwa_prepare()
