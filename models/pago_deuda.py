from odoo import models, fields, api

class PagoDeuda(models.Model):
    _name = 'ventas.pago.deuda'
    _description = 'Pago de Deuda'
    _order = 'fecha_pago desc'
    
    deuda_id = fields.Many2one(
        'ventas.deuda',
        string='Deuda',
        required=True,
        ondelete='cascade'
    )
    fecha_pago = fields.Datetime(
        string='Fecha de Pago',
        default=fields.Datetime.now,
        required=True
    )
    monto = fields.Float(string='Monto', required=True)
    tipo_pago = fields.Selection([
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia')
    ], string='Tipo de Pago', required=True, default='efectivo')
    
    # Campos relacionados
    persona_id = fields.Many2one(
        'ventas.persona',
        string='Persona',
        related='deuda_id.persona_id',
        store=True
    )
    
    
    # Restricción
    _sql_constraints = [
        ('monto_positivo', 'CHECK(monto > 0)', 'El monto debe ser positivo'),
    ]