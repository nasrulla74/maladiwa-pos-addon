import math

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = "pos.order"

    maladiwa_usd_rate = fields.Float(
        "Receipt MVR per USD",
        digits=(12, 6),
        copy=False,
        readonly=True,
    )

    maladiwa_service_product_id = fields.Many2one(
        "product.product",
        copy=False,
        readonly=True,
    )

    maladiwa_service_percent = fields.Float(
        copy=False,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            config = self.env["pos.config"].browse(
                values.get("config_id")
            )

            if not config:
                config = self.env["pos.session"].browse(
                    values.get("session_id")
                ).config_id

            if config.maladiwa_receipt_enabled:
                if not values.get("maladiwa_usd_rate"):
                    values["maladiwa_usd_rate"] = config.maladiwa_usd_rate

                if not values.get("maladiwa_service_product_id"):
                    values["maladiwa_service_product_id"] = (
                        config.maladiwa_service_product_id.id
                    )

                if "maladiwa_service_percent" not in values:
                    values["maladiwa_service_percent"] = (
                        config.maladiwa_dine_in_preset_id.service_fee_amount
                    )

        return super().create(vals_list)

    @api.constrains("maladiwa_usd_rate")
    def _check_maladiwa_rate(self):
        for order in self:
            if (
                not math.isfinite(order.maladiwa_usd_rate)
                or order.maladiwa_usd_rate < 0
            ):
                raise ValidationError(
                    _(
                        "The receipt exchange rate cannot be "
                        "negative or non-finite."
                    )
                )

    def order_receipt_generate_data(self, basic_receipt=False):
        data = super().order_receipt_generate_data(basic_receipt)
        config = self.config_id

        if not config.maladiwa_receipt_enabled or basic_receipt:
            return data

        rate = self.maladiwa_usd_rate or config.maladiwa_usd_rate
        service_product = (
            self.maladiwa_service_product_id
            or config.maladiwa_service_product_id
        )

        service_lines = self.lines.filtered(
            lambda line: line.product_id == service_product
        )

        service = sum(service_lines.mapped("price_subtotal"))
        subtotal = sum(self.lines.mapped("price_subtotal")) - service

        tax_totals = self._get_order_tax_totals()
        sign = -1 if self.is_refund_or_negative() else 1
        total = sign * tax_totals["total_amount_currency"]
        rounding = total - self.amount_total

        number = lambda value: f"{self.currency_id.round(value):.2f}"

        data["extra_data"]["maladiwa"] = {
            "subtotal": "MVR " + number(subtotal),
            "service": number(service),
            "has_service": not self.currency_id.is_zero(service),
            "service_label": (
                f"{self.maladiwa_service_percent * 100:g}% Service Charge"
            ),
            "gst": number(self.amount_tax),
            "total": "MVR " + number(total),
            "usd": number(total / rate),
            "rate": f"{rate:g}",
            "change": "MVR " + number(self.amount_return),
            "rounding": number(rounding),
            "has_rounding": not self.currency_id.is_zero(rounding),
            "reference": self.pos_reference or self.name,
            "table": str(self.table_id.table_number) if self.table_id else "",
            "guests": self.customer_count,
            "is_refund": total < 0,
            "items": [
                {
                    "id": line.id,
                    "name": (
                        line.full_product_name
                        or line.product_id.display_name
                    ),
                    "qty": f"{line.qty:g}",
                    "amount": number(line.price_subtotal),
                    "discount": f"{line.discount:g}",
                }
                for line in self.lines - service_lines
            ],
        }

        return data
