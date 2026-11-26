from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


CASHIER_GROUP = "maladiwa_pos_addon.group_maladiwa_cashier"


def is_cashier(user):
    # Keep login working between source deployment and module upgrade.
    group = user.env.ref(CASHIER_GROUP, raise_if_not_found=False)
    return bool(group and user.has_group(CASHIER_GROUP))


def require_non_cashier(env):
    if is_cashier(env.user):
        raise AccessError(
            _("This operation is not allowed for a Maladiwa cashier.")
        )


class ResUsers(models.Model):
    _inherit = "res.users"

    maladiwa_cashier = fields.Boolean(
        "Maladiwa cashier",
        compute="_compute_maladiwa_cashier",
    )

    # A non-stored field keeps staged source deployment schema-compatible.
    maladiwa_pos_config_id = fields.Many2one(
        "pos.config",
        "Assigned POS",
        compute="_compute_maladiwa_pos",
        inverse="_inverse_maladiwa_pos",
        compute_sudo=True,
        groups="base.group_system",
    )

    @api.depends("all_group_ids")
    def _compute_maladiwa_cashier(self):
        for user in self:
            user.maladiwa_cashier = is_cashier(user)

    def _compute_maladiwa_pos(self):
        parameters = self.env["ir.config_parameter"].sudo()

        for user in self:
            key = "maladiwa_pos_addon.cashier_pos.%s" % user.id

            try:
                config_id = int(parameters.get_param(key, "0"))
            except (TypeError, ValueError):
                config_id = 0

            user.maladiwa_pos_config_id = (
                self.env["pos.config"].browse(config_id).exists()
                if config_id > 0
                else False
            )

    def _inverse_maladiwa_pos(self):
        if (
            not self.env.su
            and not self.env.user.has_group("base.group_system")
        ):
            raise AccessError(
                _("Only Settings administrators may assign a cashier's POS.")
            )

        parameters = self.env["ir.config_parameter"].sudo()

        for user in self:
            parameters.set_param(
                "maladiwa_pos_addon.cashier_pos.%s" % user.id,
                str(user.maladiwa_pos_config_id.id)
                if user.maladiwa_pos_config_id
                else False,
            )

    @api.constrains(
        "group_ids",
        "maladiwa_pos_config_id",
        "company_ids",
    )
    def _check_maladiwa_cashier(self):
        for user in self.sudo():
            if not is_cashier(user):
                continue

            if any(
                user.has_group(group)
                for group in (
                    "base.group_system",
                    "base.group_erp_manager",
                    "point_of_sale.group_pos_manager",
                )
            ):
                raise ValidationError(
                    _(
                        "A Maladiwa cashier cannot also be a Settings, "
                        "Access Rights, or POS administrator. "
                        "Use separate manager and cashier accounts."
                    )
                )

            config = user.maladiwa_pos_config_id

            if (
                not config
                or not config.active
                or config.company_id not in user.company_ids
            ):
                raise ValidationError(
                    _(
                        "Assign an active POS belonging to one "
                        "of the cashier's allowed companies."
                    )
                )

    @api.model
    def _load_pos_data_fields(self, config):
        return list(
            dict.fromkeys(
                super()._load_pos_data_fields(config)
                + ["maladiwa_cashier"]
            )
        )

    @api.model
    def load_pos_data_force_loading(self):
        return True


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model_create_multi
    def create(self, vals_list):
        require_non_cashier(self.env)
        return super().create(vals_list)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        require_non_cashier(self.env)
        return super().create(vals_list)


class PosSession(models.Model):
    _inherit = "pos.session"

    @api.model_create_multi
    def create(self, vals_list):
        require_non_cashier(self.env)
        return super().create(vals_list)

    def close_session_from_ui(self, payment_method_closing=None):
        require_non_cashier(self.env)
        return super().close_session_from_ui(
            payment_method_closing or {}
        )

    def write(self, vals):
        if is_cashier(self.env.user):
            if "stop_at" in vals:
                require_non_cashier(self.env)

            if "state" in vals and (
                vals["state"] != "opened"
                or any(
                    session.state != "opening_control"
                    for session in self
                )
            ):
                require_non_cashier(self.env)

        return super().write(vals)

    def unlink(self):
        require_non_cashier(self.env)
        return super().unlink()
