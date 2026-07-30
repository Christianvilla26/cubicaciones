# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Al actualizar, todos los pagos existentes conservan el ISR histórico del 2%.
    Los pagos nuevos usarán el default del campo (3%).
    """
    cr.execute(
        """
        UPDATE pagos_order
           SET porcentaje_isr = 2.0
        """
    )
