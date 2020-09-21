# -*- coding: utf-8 -*-
{
    'name': 'Cubicaciones',
    'version': '12.0',
    'category': 'Sale',
    'author': 'Kritiam',
    'depends': [
        'base', 'mrp'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/pagos_wizzard.xml',
        'views/cubicaciones_views.xml',
        'views/nomina_views.xml',
        'views/contrato_views.xml',
        'views/pagos_views.xml',
        'report/cubication_order_templates.xml'
    ],
}