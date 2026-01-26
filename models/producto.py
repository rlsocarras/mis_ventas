from odoo import models, fields, api

class Producto(models.Model):
    _name = 'ventas.producto'
    _description = 'Producto'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    
    # Relaciones
    viaje_producto_ids = fields.One2many(
        'ventas.viaje.producto',
        'producto_id',
        string='En Viajes'
    )
    ventas_ids = fields.One2many(
        'ventas.venta',
        'viaje_producto_id',
        string='En Ventas',
        )
    deudas_ids = fields.One2many(
        'ventas.deuda',
        'viaje_producto_id',
        string='En Deudas',
        )