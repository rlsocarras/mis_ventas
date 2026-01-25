from odoo import models, fields, api
from datetime import date
import logging
_logger = logging.getLogger(__name__)

class Viaje(models.Model):
    _name = 'ventas.viaje'
    _description = 'Viaje'
    _rec_name = 'nombre'
    _order = 'fecha desc'

    # Campos indexados
    nombre = fields.Char(string='Nombre del Viaje', required=True, index=True)
    fecha = fields.Date(string='Fecha', default=fields.Date.today, index=True)

    total_invertido = fields.Float(
        string='Total Invertido', 
        compute='_compute_totales',
        store=True
    )
    ganancia_total_potencial = fields.Float(
        string='Ganancia Total Potencial',
        compute='_compute_totales',
        store=True
    )
    ganancia_total_real = fields.Float(
        string='Ganancia Total Real',
        compute='_compute_totales',
        store=True
    )
    total_efectivo = fields.Float(
        string='Total Efectivo',
        compute='_compute_totales',
        store=True
    )
    total_transferencia = fields.Float(
        string='Total Transferencia',
        compute='_compute_totales',
        store=True
    )
    total_deuda = fields.Float(
        string='Total Deuda',
        compute='_compute_totales',
        store=True
    )
    
    total_vendido = fields.Float(
        string='Total vendido',
        compute='_compute_totales',
        store=True
    )

    total_por_vender = fields.Float(
        string='Total por vender',
        compute='_compute_totales',
        store=True
    )
    total_dinero_en_mano = fields.Float(
        string='Total dinero en mano',
        compute='_compute_totales',
        store=True
    )
    
    
    # Relaciones
    viaje_producto_ids = fields.One2many(
        'ventas.viaje.producto',
        'viaje_id',
        string='Productos del Viaje'
    )
    ventas_ids = fields.One2many(
        'ventas.venta',
        'viaje_id',
        string='Ventas del Viaje'
    )

    deudas_ids = fields.One2many(
        'ventas.deuda',
        'viaje_id',
        string='Deudas del Viaje'
    )

     # Agregar índices
    _order = 'fecha desc, nombre'

    
   

    @api.depends('viaje_producto_ids', 'ventas_ids', 'deudas_ids', 'deudas_ids.pagos_ids', 
                 'deudas_ids.estado', 'deudas_ids.monto_pendiente')
    def _compute_totales(self):
        for viaje in self:
            # Totales de inversión
            viaje.total_invertido = sum(
                viaje.viaje_producto_ids.mapped('total_invertido')
            )
            
            # Ganancia potencial
            viaje.ganancia_total_potencial = sum(
                viaje.viaje_producto_ids.mapped('total_ganancia_potencial')
            )

           
            
            # Totales de ventas por tipo de pago
            ventas = viaje.ventas_ids

            # Totales de deudas pagadas por tipo de pago que se suma al efectivo y la transferenci
            deudas_pendientes = viaje.deudas_ids
            #total de dinero real de las deudas
            deudas_pagadas_efectivo = sum(
                deudas_pendientes.mapped('pagos_ids').filtered(lambda p: p.tipo_pago == 'efectivo').mapped('monto')
            )
            
            deudas_pagadas_transferencia = sum(
                deudas_pendientes.mapped('pagos_ids').filtered(lambda p: p.tipo_pago == 'transferencia').mapped('monto')
            )

            viaje.total_efectivo = sum(
                ventas.filtered(lambda v: v.tipo_pago == 'efectivo')
                .mapped('total')
            )  + deudas_pagadas_efectivo
            viaje.total_transferencia = sum(
                ventas.filtered(lambda v: v.tipo_pago == 'transferencia')
                .mapped('total')
            ) + deudas_pagadas_transferencia
            
            # Ganancia real (solo ventas pagadas)
            ventas_pagadas = ventas.filtered(
                lambda v: v.tipo_pago in ['efectivo', 'transferencia']
            )
            viaje.ganancia_total_real = sum(
                ventas_pagadas.mapped('ganancia')
            )
            
            # Total deuda
            viaje.total_deuda  = sum(
                deudas_pendientes.mapped('monto_pendiente')
            )
            
            viaje.total_dinero_en_mano=viaje.total_efectivo + viaje.total_transferencia
            viaje.total_vendido=viaje.total_dinero_en_mano + viaje.total_deuda


    def action_crear_venta(self):
        """Abrir formulario para crear una nueva venta"""
        self.ensure_one()
        return {
        'type': 'ir.actions.act_window',
        'name': 'Nueva Venta',
        'res_model': 'ventas.venta',
        'view_mode': 'form',
        'target': 'current',
        'context': {
            'default_viaje_id': self.id,
            'default_tipo_pago': 'efectivo',
            }
        }
def unlink(self):
    for viaje in self:
        if viaje.ventas_ids:
            raise models.ValidationError(
                'No se puede eliminar un viaje que tiene ventas registradas'
            )
        if viaje.deudas_ids.filtered(lambda d: d.estado != 'pagado'):
            raise models.ValidationError(
                'No se puede eliminar un viaje con deudas pendientes'
            )
    return super().unlink()
