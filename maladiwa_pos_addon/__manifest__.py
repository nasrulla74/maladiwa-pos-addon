{
    "name": "Maladiwa POS Addon",
    "version": "20.0.1.0.0",
    "summary": "Dine-in service charge and Maladiwa MVR/USD restaurant receipt",
    "category": "Sales/Point of Sale",
    "author": "Maladiwa",
    "license": "LGPL-3",
    "depends": ["pos_restaurant"],
    "data": [
        "views/settings.xml",
        "views/receipt.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "maladiwa_pos_addon/static/src/js/receipt.js",
        ],
    },
    "installable": True,
    "application": False,
}
