{
    "name": "Maladiwa POS Addon",
    "version": "20.0.1.0.5",
    "summary": "Dine-in service charge and Maladiwa MVR/USD restaurant receipt",
    "category": "Sales/Point of Sale",
    "author": "Maladiwa",
    "license": "LGPL-3",
    "depends": ["pos_restaurant"],
    "data": [
        "security/cashier_security.xml",
        "views/settings.xml",
        "views/receipt.xml",
        "views/cashier_users.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "maladiwa_pos_addon/static/src/js/receipt.js",
            "maladiwa_pos_addon/static/src/js/full_receipt_only.js",
            "maladiwa_pos_addon/static/src/js/cashier_permissions.js",
            "maladiwa_pos_addon/static/src/xml/cashier_menu.xml",
        ],
    },
    "installable": True,
    "application": False,
}
