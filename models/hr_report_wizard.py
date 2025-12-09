from odoo import models, fields
from odoo.exceptions import UserError
import io
import base64
from datetime import date

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class InvoiceEmployeeReportWizard(models.TransientModel):
    _name = 'hr.report.wizard'
    _description = 'Reporte de facturas no pagadas (RRHH)'

    date_from = fields.Date(string='Fecha desde', required=True)
    date_to = fields.Date(string='Fecha hasta', required=True)
    user_id = fields.Many2one(
        'res.users',
        string='Usuario',
        help="Usuario responsable de la factura."
    )
    move_type_info = fields.Char(string='Tipo', default='Factura de cliente', readonly=True)
    state_info = fields.Char(string='Estado', default='Registrado', readonly=True)
    payment_state_info = fields.Char(string='Estado de pago', default='Sin pagar', readonly=True)

    def action_generate_xlsx(self):
        self.ensure_one()
        if not xlsxwriter:
            raise UserError("El módulo python 'xlsxwriter' no está instalado en el servidor.")

        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ]
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))

        moves = self.env['account.move'].search(domain)

        data_by_partner = {}
        for move in moves:
            partner = move.partner_id
            if not partner:
                continue

            codigo = partner.x_studio_codigo or ''
            raw_name = partner.name or ''
            empleado = raw_name

            if codigo:
                patterns = [
                    f"{codigo} ",
                    f"[{codigo}] ",
                    f"[{codigo}]",
                    f"{codigo}-",
                    f"{codigo} - ",
                ]
                for p in patterns:
                    if empleado.startswith(p):
                        empleado = empleado[len(p):]
                        break
                else:
                    if empleado.startswith(codigo):
                        empleado = empleado[len(codigo):].lstrip()

            key = partner.id
            if key not in data_by_partner:
                data_by_partner[key] = {
                    'codigo_empleado': codigo,
                    'empleado': empleado,
                    'monto': 0.0,
                }
            data_by_partner[key]['monto'] += move.amount_total

        codigo_deduccion = ''
        nombre_deduccion = ''
        page_name = ''
        login = self.user_id.login if self.user_id else False

        if login == 'delta@adi.com':
            codigo_deduccion = 'CAFECOM'
            nombre_deduccion = 'CAFETERIA COMALI'
            page_name = 'CAFETERIA COMALI'
        elif login == 'zeta@adi.com':
            codigo_deduccion = 'TC'
            nombre_deduccion = 'TIENDA DE CONSUMO'
            page_name = 'TIENDA DE CONSUMO'

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(page_name)

        header_fmt = workbook.add_format({'bold': True})
        amount_fmt = workbook.add_format({'num_format': '0.00'})

        sheet.write(0, 0, 'CodigoEmpleado', header_fmt)
        sheet.write(0, 1, 'Empleado', header_fmt)
        sheet.write(0, 2, 'CodigoDeduccion', header_fmt)
        sheet.write(0, 3, 'NombreDeduccion', header_fmt)
        sheet.write(0, 4, 'Monto', header_fmt)

        def _codigo_sort_key(vals):
            code = vals['codigo_empleado'] or ''
            try:
                return int(code)
            except ValueError:
                return float('inf')

        sorted_rows = sorted(data_by_partner.values(), key=_codigo_sort_key)

        row = 1
        for vals in sorted_rows:
            sheet.write(row, 0, vals['codigo_empleado'])
            sheet.write(row, 1, vals['empleado'])
            sheet.write(row, 2, codigo_deduccion)
            sheet.write(row, 3, nombre_deduccion)
            sheet.write_number(row, 4, vals['monto'], amount_fmt)  # 2 decimales
            row += 1

        workbook.close()
        output.seek(0)
        xlsx_data = output.read()

        file_name = "Reporte_Facturas_Empleados_%s.xlsx" % date.today().strftime('%Y%m%d')
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=1' % attachment.id,
            'target': 'self',
        }