from odoo import models, fields, api
from datetime import timedelta

class PagoDeuda(models.Model):
    _name = 'ventas.viajes.pago'
    _description = 'Pago Parcial de Deuda'
    _order = 'fecha desc'
    _rec_name = 'display_name'
    
    deuda_id = fields.Many2one('ventas.viajes.deuda', string='Deuda', required=True, ondelete='cascade')
    persona_id = fields.Many2one('ventas.viajes.persona', string='Persona', related='deuda_id.persona_id', store=True)
    viaje_id = fields.Many2one('ventas.viajes.viaje', string='Viaje', related='deuda_id.viaje_id', store=True)
    
    monto = fields.Float(string='Monto del Pago', required=True)
    fecha = fields.Date(string='Fecha del Pago', default=fields.Date.today, required=True)
    tipo_pago = fields.Selection([
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('cheque', 'Cheque'),
        ('otro', 'Otro'),
    ], string='Tipo de Pago', default='efectivo', required=True)
    
    observaciones = fields.Text(string='Observaciones')
    state = fields.Selection([
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
    ], string='Estado', default='confirmado')
    
    display_name = fields.Char(
        string='Nombre Mostrado',
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('deuda_id.display_name', 'fecha', 'monto')
    def _compute_display_name(self):
        """Calcula el nombre mostrado para el pago"""
        for pago in self:
            deuda_nombre = pago.deuda_id.display_name or 'Sin Deuda'
            pago.display_name = f"Pago {pago.fecha} - {deuda_nombre} - ${pago.monto:.2f}"
    
    @api.model
    def create(self, vals):
        """Al crear un pago, actualizar la deuda asociada"""
        pago = super(PagoDeuda, self).create(vals)
        
        if pago.state == 'confirmado':
            # Actualizar la deuda
            pago.deuda_id.saldo_anterior = pago.deuda_id.monto_pagado
            pago.deuda_id.monto_pagado += pago.monto
            pago.deuda_id.fecha_ultimo_pago = pago.fecha
            
            # Si se completa el pago, marcar fecha_pago
            if pago.deuda_id.monto_pendiente <= 0:
                pago.deuda_id.fecha_pago = pago.fecha
                
                # Actualizar venta asociada
                if pago.deuda_id.venta_id:
                    pago.deuda_id.venta_id.write({
                        'state': 'pagada',
                        'tipo_pago': pago.tipo_pago,
                    })
        
        return pago
    
    def write(self, vals):
        """Al actualizar un pago, ajustar la deuda si cambia el monto"""
        if 'monto' in vals or 'state' in vals:
            for pago in self:
                deuda = pago.deuda_id
                
                # Guardar valores anteriores
                monto_anterior = pago.monto
                estado_anterior = pago.state
                
                # Primero revertir el pago anterior
                if estado_anterior == 'confirmado':
                    deuda.monto_pagado -= monto_anterior
                
                # Escribir nuevos valores
                result = super(PagoDeuda, pago).write(vals)
                
                # Aplicar nuevo pago si está confirmado
                if pago.state == 'confirmado':
                    deuda.monto_pagado += pago.monto
                    deuda.fecha_ultimo_pago = pago.fecha
                    
                    # Si se completa el pago, marcar fecha_pago
                    if deuda.monto_pendiente <= 0:
                        deuda.fecha_pago = pago.fecha
                else:
                    # Si se cancela el pago
                    deuda.fecha_ultimo_pago = None
                    
                # Recalcular estado
                deuda._compute_state()
                
                return result
        
        return super(PagoDeuda, self).write(vals)
    
    def unlink(self):
        """Al eliminar un pago, revertir en la deuda"""
        for pago in self:
            if pago.state == 'confirmado':
                pago.deuda_id.monto_pagado -= pago.monto
                pago.deuda_id._compute_state()
        
        return super(PagoDeuda, self).unlink()