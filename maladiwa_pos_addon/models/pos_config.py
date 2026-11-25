import math

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    maladiwa_receipt_enabled = fields.Boolean("Maladiwa receipt")

    maladiwa_usd_rate = fields.Float(
        "MVR per USD",
        default=15.42,
        digits=(12, 6),
    )

    maladiwa_restaurant_name = fields.Char(
        "Receipt restaurant name",
        default="Maladiwa Melon Restaurant",
    )

    maladiwa_bank_mvr = fields.Char(
        "MVR bank account",
        default="7730000467579",
    )

    maladiwa_bank_usd = fields.Char(
        "USD bank account",
        default="7730000467584",
    )

    maladiwa_gst_tax_id = fields.Many2one(
        "account.tax",
        "GST",
        check_company=True,
    )

    maladiwa_service_product_id = fields.Many2one(
        "product.product",
        "Service charge product",
        check_company=True,
        copy=False,
    )

    maladiwa_dine_in_preset_id = fields.Many2one(
        "pos.preset",
        "Maladiwa dine-in",
        copy=False,
    )

    maladiwa_takeaway_preset_id = fields.Many2one(
        "pos.preset",
        "Maladiwa takeaway",
        copy=False,
    )

    @api.constrains(
        "maladiwa_receipt_enabled",
        "maladiwa_usd_rate",
        "currency_id",
    )
    def _check_maladiwa_currency(self):
        for config in self:
            if not config.maladiwa_receipt_enabled:
                continue

            if config.currency_id.name != "MVR":
                raise ValidationError(
                    _("Maladiwa receipts require the POS currency to be MVR.")
                )

            if (
                not math.isfinite(config.maladiwa_usd_rate)
                or config.maladiwa_usd_rate <= 0
            ):
                raise ValidationError(
                    _("MVR per USD must be greater than zero.")
                )

    def action_maladiwa_prepare(self):
        self.ensure_one()

        if not self.env.user.has_group("point_of_sale.group_pos_manager"):
            raise UserError(
                _("Only POS managers may prepare this configuration.")
            )

        self.check_access("write")

        if self.current_session_id and self.current_session_id.state != "closed":
            raise UserError(
                _("Close this POS session before preparing Maladiwa settings.")
            )

        if self.currency_id.name != "MVR":
            raise UserError(
                _("Set this POS currency to MVR before preparing the addon.")
            )

        if (
            not math.isfinite(self.maladiwa_usd_rate)
            or self.maladiwa_usd_rate <= 0
        ):
            raise UserError(_("MVR per USD must be greater than zero."))

        if not self.module_pos_restaurant:
            raise UserError(_("Enable restaurant mode for this POS first."))

        company = self.company_id
        tax = self.maladiwa_gst_tax_id

        if not tax:
            raise UserError(
                _(
                    "Select your company's sales GST tax first. "
                    "Start with 16% in Odoo Taxes."
                )
            )

        if (
            tax.company_id != company
            or tax.type_tax_use != "sale"
            or tax.amount_type != "percent"
        ):
            raise UserError(
                _(
                    "Choose a percentage sales GST tax "
                    "belonging to this company."
                )
            )

        product = self.maladiwa_service_product_id

        if not product:
            product = self.env["product.product"].create({
                "name": "Service Charge",
                "type": "service",
                "company_id": company.id,
                "list_price": 0,
                "available_in_pos": False,
                "purchase_ok": False,
                "taxes_id": [fields.Command.set(tax.ids)],
            })

        dine_in = self.maladiwa_dine_in_preset_id

        if not dine_in:
            dine_in = self.env["pos.preset"].create({
                "name": "Dine In - " + self.name,
                "service_fee": True,
                "service_fee_type": "percent",
                "service_fee_amount": 0.10,
                "service_fee_based_on": "post_discount",
                "service_fee_product_id": product.id,
                "use_guest": True,
            })

        takeaway = self.maladiwa_takeaway_preset_id

        if not takeaway:
            takeaway = self.env["pos.preset"].create({
                "name": "Takeaway - " + self.name,
                "service_fee": False,
            })

        presets = self.available_preset_ids
        master_dine_in = self.env.ref(
            "pos_restaurant.pos_takein_preset",
            raise_if_not_found=False,
        )

        if master_dine_in:
            presets -= master_dine_in

        self.write({
            "maladiwa_gst_tax_id": tax.id,
            "maladiwa_service_product_id": dine_in.service_fee_product_id.id,
            "maladiwa_dine_in_preset_id": dine_in.id,
            "maladiwa_takeaway_preset_id": takeaway.id,
            "use_presets": True,
            "available_preset_ids": [
                fields.Command.set((presets | dine_in | takeaway).ids)
            ],
            "default_preset_id": dine_in.id,
            "maladiwa_receipt_enabled": True,
        })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Maladiwa POS prepared"),
                "message": _(
                    "Set customer GST on your food products, then reopen POS. "
                    "Takeaway has no service charge."
                ),
                "sticky": True,
                "next": {
                    "type": "ir.actions.client",
                    "tag": "reload",
                },
            },
        }
