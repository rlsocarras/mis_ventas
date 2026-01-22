from odoo import models, fields, api
from datetime import timedelta

class PagoParcialWizard(models.TransientModel):
    _name = 'ventas.viajes.pago.parcial.wizard'
    _description = 'Wizard para Pago Parcial'
    
    deuda_id = fields.Many2one('ventas.viajes.deuda', string='Deuda', required=True, readonly=True)
    persona_id = fields.Many2one('ventas.viajes.persona', string='Persona', related='deuda_id.persona_id', readonly=True)
    monto_total = fields.Float(string='Monto Total', related='deuda_id.monto', readonly=True)
    monto_pagado = fields.Float(string='Monto Ya Pagado', related='deuda_id.monto_pagado', readonly=True)
    monto_pendiente = fields.Float(string='Monto Pendiente', related='deuda_id.monto_pendiente', readonly=True)
    monto_maximo = fields.Float(string='Monto Máximo', readonly=True)
    
    monto = fields.Float(string='Monto a Pagar', required=True)
    descripcion = fields.Char(string='Descripción', default='Pago parcial')
    
    @api.onchange('monto')
    def _onchange_monto(self):
        """Validar que el monto no exceda el pendiente"""
        if self.monto > self.monto_pendiente:
            return {
                'warning': {
                    'title': 'Monto Excedido',
                    'message': f'El monto no puede ser mayor al pendiente (${self.monto_pendiente:.2f})'
                }
            }
    
    def action_confirmar_pago(self):
        """Confirmar el pago parcial"""
        self.ensure_one()
        
        # Validaciones
        if self.monto <= 0:
            raise models.ValidationError('El monto debe ser mayor a 0')
        
        if self.monto > self.deuda_id.monto_pendiente:
            raise models.ValidationError(f'El monto no puede exceder el pendiente (${self.deuda_id.monto_pendiente:.2f})')
        
        # Actualizar deuda
        self.deuda_id.monto_pagado += self.monto
        self.deuda_id.fecha_pago = fields.Date.today() if self.deuda_id.monto_pendiente <= 0 else False
        
        # Mostrar mensaje de confirmación
        mensaje = f'Pago de ${self.monto:.2f} registrado exitosamente.\n'
        mensaje += f'Saldo pendiente: ${self.deuda_id.monto_pendiente:.2f}\n'
       
        
        if self.deuda_id.monto_pendiente <= 0:
            mensaje += '\n¡Deuda completamente pagada!'
        
        return {
            'type': 'ir.actions.act_window_close',
            'context': {'success_message': mensaje}
        }