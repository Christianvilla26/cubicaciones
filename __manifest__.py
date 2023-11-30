# -*- coding: utf-8 -*-
{
    "name": "Cubicaciones",
    "version": "15.0",
    "category": "Sale",
    "author": "Kritiam",
    "depends": ["base", "mrp", "account", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/pagos_wizzard.xml",
        "views/cubicaciones_views.xml",
        "views/partidas_views.xml",
        "views/nomina_views.xml",
        "views/contrato_views.xml",
        "views/pagos_views.xml",
        "views/nivel_views.xml",
        "report/cubication_order_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cubicaciones/static/src/css/style.css"
        ]
    }
}
