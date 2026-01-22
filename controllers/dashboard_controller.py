from odoo import http
from odoo.http import request
import json
from datetime import datetime, timedelta

class DashboardController(http.Controller):
    
    @http.route('/mis_ventas/get_dashboard_data', type='json', auth='user')
    def get_dashboard_data(self, **kwargs):
        """Retorna datos para el dashboard"""
        user = request.env.user
        
        # Obtener datos de viajes
        viajes = request.env['ventas.viajes.viaje'].search([])
        
        # Calcular estadísticas
        total_invertido = sum(v.total_invertido for v in viajes)
        total_ventas = sum(v.total_ventas for v in viajes)
        total_ganancia_real = sum(v.ganancia_real for v in viajes)
        total_deuda = sum(v.total_deuda for v in viajes)
        
        # Viajes por mes (últimos 6 meses)
        meses_data = []
        hoy = datetime.now()
        for i in range(5, -1, -1):
            mes = hoy - timedelta(days=30*i)
            viajes_mes = viajes.filtered(
                lambda v: v.fecha and v.fecha.month == mes.month and v.fecha.year == mes.year
            )
            meses_data.append({
                'mes': mes.strftime('%b'),
                'ganancia': sum(v.ganancia_real for v in viajes_mes),
                'ventas': sum(v.total_ventas for v in viajes_mes)
            })
        
        return {
            'total_viajes': len(viajes),
            'total_invertido': total_invertido,
            'total_ventas': total_ventas,
            'total_ganancia_real': total_ganancia_real,
            'total_deuda': total_deuda,
            'roi_promedio': (total_ganancia_real / total_invertido * 100) if total_invertido > 0 else 0,
            'meses_data': meses_data,
            'viajes_rentables': len([v for v in viajes if v.ganancia_real > 0]),
            'viajes_perdida': len([v for v in viajes if v.ganancia_real < 0]),
        }