from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.http.session import check
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.utils import ensure_db
from odoo.addons.point_of_sale.controllers.main import PosController

from ..models.cashier_security import is_cashier


ENTRY_URL = "/maladiwa/pos"


def assigned_pos(user):
    config = user.sudo().maladiwa_pos_config_id

    if (
        not config
        or not config.active
        or config.company_id not in user.company_ids
    ):
        raise AccessError(
            _("Ask your manager to assign an active POS to your account.")
        )

    return config


class CashierHome(Home):
    def _login_redirect(self, uid, redirect=None):
        destination = super()._login_redirect(
            uid,
            redirect=redirect,
        )

        # Preserve MFA until the session is fully authenticated.
        if request.session.uid == uid:
            user = request.env["res.users"].sudo().browse(uid)

            if is_cashier(user):
                return ENTRY_URL

        return destination

    @http.route()
    def web_client(self, s_action=None, **kw):
        ensure_db()

        if request.session.uid:
            check(request.session, request)
            request.update_env(user=request.session.uid)

            if is_cashier(request.env.user):
                return request.redirect(ENTRY_URL, code=303)

        return super().web_client(s_action=s_action, **kw)


class CashierPos(PosController):
    @http.route(
        ENTRY_URL,
        type="http",
        auth="user",
        readonly=True,
    )
    def maladiwa_pos(self, **kw):
        user = request.env.user

        if not is_cashier(user):
            return request.redirect("/odoo", code=303)

        config = assigned_pos(user)

        if (
            not config.current_session_id
            or config.current_session_id.state
            not in ("opening_control", "opened")
        ):
            return request.render(
                "maladiwa_pos_addon.cashier_register_closed",
                status=409,
            )

        return request.redirect(
            "/pos/ui/%s" % config.id,
            code=303,
        )

    @http.route()
    def pos_web(
        self,
        config_id=False,
        from_backend=False,
        subpath=None,
        **kw,
    ):
        if is_cashier(request.env.user):
            config = assigned_pos(request.env.user)

            if str(config_id) != str(config.id):
                return request.redirect(ENTRY_URL, code=303)

            if (
                not config.current_session_id
                or config.current_session_id.state
                not in ("opening_control", "opened")
            ):
                return request.redirect(ENTRY_URL, code=303)

            from_backend = False

        return super().pos_web(
            config_id=config_id,
            from_backend=from_backend,
            subpath=subpath,
            **kw,
        )
