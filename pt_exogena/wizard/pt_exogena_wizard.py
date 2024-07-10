# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PtExogenaWizard(models.TransientModel):
    _name = 'pt.exogena.wizard'
    _description = 'Pt Exogena Wizard'

    report_type = fields.Selection([('1001', '1001'), ('1003', '1003'), ('1004', '1004'), ('1005', '1005'), ('1006', '1006'), ('1007', '1007'), ('1008', '1008'), ('1009', '1009')], string='Report Type', default='1001')
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True, default=fields.Datetime.now)
    pt_config_accounts_id = fields.Many2one('pt.config.accounts', string='Format Configuration to use')

    def getaccountssummarized(self, data):
        # Get the accounts to be summarized
        records = []
        date_start = data['date_start']
        date_end = data['date_end']
        company_id = self.env.company.id

        for record in data["pt_config_accounts_id"].pt_config_account_line_ids:
            print(record.pt_config_accounts_concepts_line_ids)
            for line in record.pt_config_accounts_concepts_line_ids:
                acc_moves = self.env['account.move.line'].read_group([('account_id', '=', line.account_id.id),
                                                                      ('date', '>=', date_start),
                                                                      ('date', '<=', date_end),
                                                                      ('company_id', '=', company_id)],
                                                                     ['debit', 'credit', 'balance'], ['partner_id'])
                for acc_move in acc_moves:
                    data ={
                        'code': record.code,
                        'partner_id': acc_move['partner_id'][0],
                        'account_id': line.account_id.id,
                        'calculation_type': line.calculation_type,
                        'column_number': line.column_number,
                        'debit': acc_move['debit'],
                        'credit': acc_move['credit'],
                        'balance': acc_move['balance'],
                    }
                    records.append(data)
        return records

    def generate_xlsx_report(self):
        datas = {'date_start': self.start_date, 'date_end': self.end_date, 'pt_config_accounts_id': self.pt_config_accounts_id}
        format_data = self.getaccountssummarized(data=datas)
        if self.report_type == '1001':
           columnas = ['Concepto', 'Tipo de documento', 'Número identificación', 'Primer apellido del informado',
                       'Segundo apellido del informado', 'Primer nombre del informado', 'Otros nombres del informado',
                       'Razón social informado', 'Dirección',	'Código dpto', 'Código mcp',
                       'País de Residencia o domicilio', 'Pago o abono en cuenta deducible',
                       'Pago o abono en cuenta NO deducible', 'IVA mayor valor del costo o gasto, deducible',
                       'IVA mayor valor del costo o gasto no deducible', 'Retención en la fuente practicada Renta',
                       'Retención en la fuente asumida Renta', 'Retención en la fuente practicada IVA Régimen común',
                       'Retención en la fuente practicada IVA no domiciliados']
        elif self.report_type == '1003':
            columnas = ['Concepto', 'Tipo de documento', 'Número identificación del informado', 'DV',
                        'Primer apellido del informado', 'Segundo apellido del informado', 'Primer nombre del informado',
                        'Otros nombres del informado', 'Razón social informado', 'Dirección', 'Código del Departamento',
                        'Código del Municipio', 'Valor acumulado del pago o abono sujeto a Retención en la fuente',
                        'Retención que le practicaron']
        elif self.report_type == '1004':
            columnas = ['Concepto','Tipo de documento del Tercero', 'Número de Identificación del Tercero',
                        'Primer apellido', 'Segundo apellido', 'Primer nombre', 'Otros nombres', 'Razón Social',
                        'Dirección', 'Código dpto', 'Código mcp', 'Código País', 'Correo Electrónico' ,
                        'Valor del descuento tributario total del año',
                        'Valor del descuento tributario efectivamente solicitado en el año gravable']
        elif self.report_type == '1005':
            columnas = ['Tipo de Documento', 'Numero de identificación del informado', 'DV', 'Primer apellido del informado',
                        'Segundo apellido del informado', 'Primer nombre del informado', 'Otros nombres del informado',
                        'Razón social informado', 'Impuesto descontable',
                        'IVA resultante por devoluciones en ventas anuladas rescindidas o resueltas']
        elif self.report_type == '1006':
            columnas = ['Tipo de Documento', 'Número identificación', 'DV', 'Primer apellido del informado',
                        'Segundo apellido del informado', 'Primer nombre del informado', 'Otros nombres del informado',
                        'Razón social informado', 'Impuesto generado',
                        'IVA recuperado en devoluciones en compras anuladas rescindidas o resueltas',
                        'Impuesto nacional al consumo' ]
        elif self.report_type == '1007':
            columnas = ['Concepto', 'Tipo de documento', 'Número identificación del informado',
                        'Primer apellido del informado', 'Segundo apellido del informado', 'Primer nombre del informado',
                        'Otros nombres del informado', 'Razón social informado', 'País de residencia o domicilio',
                        'Ingresos brutos recibidos', 'Devoluciones', 'rebajas y descuentos']
        elif self.report_type == '1008':
            columnas = ['Concepto', 'Tipo de documento', 'Número identificación', 'DV', 'Primer apellido deudor',
                        'Segundo apellido deudor', 'Primer nombre deudor', 'Otros nombres deudor', 'Razón social deudor',
                        'Dirección', 'Código dpto', 'Código mcp', 'País de residencia o domicilio',
                        'Saldo cuentas por cobrar al 31-12']
        elif self.report_type == '1009':
            columnas = ['Concepto',	'Tipo de documento'	'Número identificación', 'DV', 'Primer apellido',
                        'Segundo apellido',	'Primer nombre', 'Otros nombres', 'Razón social', 'Dirección', 'Código dpto',
                        'Código mcp', 'País de residencia o domicilio', 'Saldo cuentas por pagar al 31-12']
        elif self.report_type == '1010':
            columnas = ['Tipo de documento', 'Número identificación socio o accionista', 'DV',
                        'Primer apellido socio o accionista', 'Segundo apellido socio o accionista',
                        'Primer nombre del socio o accionista', 'Otros nombres socio o accionista', 'Razón social',
                        'Dirección', 'Código dpto',	'País de residencia o domicilio',
                        'Valor patrimonial acciones o aportes al 31-12', 'Porcentaje de participación',
                        'Porcentaje de participación (posición decimal)' ]
        elif self.report_type == '1647':
            columnas = ['concepto',	'Tipo de documento de quien se recibe el ingreso',
                        'Número identificación de quien recibe el ingreso', 'DV',
                        'Primer apellido de quien se recibe el ingreso','Segundo apellido de quien se recibe el ingreso',
                        'Primer nombre de quien se recibe el ingreso', 'Otros nombres de quien se recibe el ingreso',
                        'Razón social de quien se recibe el ingreso',
                        'País de residencia o domicilio de quien se recibe el ingreso', 'Valor total de la operación',
                        'Valor ingreso reintegrado transferido distribuido al tercero',
                        'Valor retención reintegrada transferida  distribuida al tercero',
                        'Tipo de documento del tercero para quien se recibió el ingreso',
                        'Identificación del tercero para quien se recibió el ingreso',
                        'Primer apellido del tercero para quien se recibió el ingreso',
                        'Segundo apellido del tercero par quien se recibió el ingreso',
                        'Primer nombre del tercero para quien se recibió el ingreso',
                        'Otros nombres del tercero para quien se recibió el ingreso',
                        'Razón social del tercero para quien se recibió el ingreso',
                        'Dirección', 'Código dpto',	'Código mcp', 'País de residencia o domicilio']
        elif self.report_type == '2275':
            columnas = ['concepto',	'Tipo de documento del tercero', 'Número identificación del tercero',
                        'Primer apellido del informado', 'Segundo apellido del informado', 'Primer nombre del informado',
                        'Otros nombres del informado', 'Razón social', 'Dirección',	'Código dpto', 'Código mcp',
                        'Código País', 'Correo electrónico',
                        'Valor del ingreso no constitutivo de renta ni ganancia ocasional solicitado']
        elif self.report_type == '2276':
            columnas = ['Entidad Informante', 'Tipo de documento del beneficiario',
                        'Número de Identificación del beneficiario',
                        'Primer Apellido del beneficiario', 'Segundo Apellido del beneficiario',
                        'Primer Nombre del beneficiario','Otros Nombres del beneficiario', 'Dirección del beneficiario',
                        'Departamento del beneficiario', 'Municipio del beneficiario', 'País del beneficiario',
                        'Pagos por Salarios', 'Pagos por emolumentos eclesiásticos', 'Pagos por honorarios',
                        'Pagos por servicios', 'Pagos por comisiones', 'Pagos por prestaciones sociales',
                        'Pagos por viáticos', 'Pagos por gastos de representación',
                        'Pagos por compensaciones trabajo asociado cooperativo', 'Otros pagos',
                        'Cesantías e intereses de cesantías efectivamente pagadas, consignadas o reconocidas en el periodo',
                        'Pensiones de Jubilación, vejez o invalidez', 'Total Ingresos brutos de rentas de trabajo y pensión',
                        'Aportes Obligatorios por Salud', 'Aportes obligatorios a fondos de pensiones y solidaridad pensional y Aportes voluntarios al - RAIS',
                        'Aportes voluntarios a fondos de pensiones voluntarias', 'Aportes a cuentas AFC', 'Aportes a cuentas AVC',
                        'Valor de las retenciones en la fuente por pagos de rentas de trabajo o pensiones',
                        'Pagos realizados con bonos electrónicos o de papel de servicio, cheques, tarjetas, vales, etc.	Apoyos económicos no reembolsables o condonados, entregados por el Estado o financiados con recursos públicos, para financiar programas educativos',
                        'Pagos por alimentación mayores a 41 UVT', 'Pagos por alimentación hasta a 41 UVT',
                        'Identificación del fideicomiso o contrato', 'Tipo documento participante en contrato de colaboración',
                        'Identificación participante en contrato colaboración']

        switch_id = {
            'rut': '31',
            'id_document': '13',
            'national_citizen_id': '13',
            'id_card': '12',
            'passport': '41',
            'foreigner_id_card': '22',
            'external_id': '42',
            'diplomatic_card': '42',
            'residence_document': '21',
            'civil_registration': '11',
        }

        cod_paises = {'AF': 13, 'AL': 17, 'DE': 23, 'AD': 37, 'AO': 40, 'AI': 41, 'AG': 43, 'AQ': 0, 'SA': 53, 'DZ': 59,
                      'AR': 63, 'AM': 26, 'AW': 27, 'AU': 69, 'AT': 72, 'AZ': 74, 'BS': 77, 'BH': 80, 'BD': 81, 'BB': 83,
                      'BZ': 88, 'BJ': 229,'BM': 90, 'BT': 119, 'BY': 91, 'MM': 93, 'BO': 97, 'BQ': 0, 'BA': 29, 'BW': 101,
                      'BR': 105, 'BN': 108, 'BG': 111, 'BF': 0, 'BI': 115, 'BE': 0, 'CV': 127, 'KH': 141, 'CM': 145, 'CA': 149,
                      'TD': 203, 'CL': 211, 'CN': 215, 'CY': 221, 'CO': 169, 'KM': 173, 'CG': 177, 'KP': 187, 'KR': 190,
                      'CR': 196, 'CI': 193, 'HR': 198, 'CU': 199, 'CW': 0, 'DK': 232, 'DM': 235, 'UM': 0, 'EC': 239,
                      'EG': 240, 'SV': 242, 'AE': 244, 'ER': 243, 'SK': 246, 'SI': 247, 'ES': 245, 'PS': 897, 'US': 249,
                      'EE': 251, 'ET': 253, 'RU': 676, 'FJ': 870, 'PH': 267, 'FI': 271, 'FR': 275, 'GA': 0, 'GM': 285,
                      'GE': 287, 'GH': 289, 'GI': 293, 'GD': 297, 'GR': 301, 'GL': 305, 'GP': 309, 'GU': 313, 'GT': 317,
                      'GY': 337, 'GF': 325, 'GG': 0, 'GN': 329, 'GQ': 331, 'GW': 334, 'HT': 341, 'NL': 573, 'HN': 345,
                      'HK': 351, 'HU': 355, 'IN': 361, 'ID': 365, 'IQ': 369, 'IE': 375, 'IR': 372, 'BV': 0, 'NF': 0, 'IM': 0,
                      'CX': 0, 'IS': 379, 'KY': 0, 'CC': 0, 'CK': 0, 'FO': 0, 'GS': 0, 'HM': 0, 'FK': 0, 'MP': 0, 'MH': 0,
                      'PN': 0, 'SB': 0, 'TC': 0, 'VG': 0, 'VI': 0, 'AX': 0, 'IL': 383, 'IT': 386, 'JM': 391, 'JP': 0,
                      'JE': 0, 'JO': 403, 'KZ': 0, 'KE': 410, 'KG': 0, 'KI': 411, 'XK': 0, 'KW': 413, 'LA': 0, 'LS': 426,
                      'LV': 429, 'LR': 434, 'LY': 0, 'LI': 440, 'LT': 443, 'LU': 445, 'LB': 0, 'MO': 447, 'MK': 0,
                      'MG': 450, 'MY': 0, 'MW': 458, 'MV': 461, 'ML': 464, 'MT': 467, 'MA': 474, 'MQ': 477, 'MU': 485,
                      'MR': 488, 'YT': 0, 'FM': 0, 'MD': 496, 'MN': 497, 'ME': 0, 'MS': 0, 'MZ': 505, 'MX': 0, 'MC': 0,
                      'NR': 508, 'NP': 517, 'NI': 521, 'NG': 528, 'NU': 0, 'NO': 538, 'NC': 542, 'NZ': 0, 'NE': 0, 'OM': 0,
                      'PK': 0, 'PW': 0, 'PA': 0, 'PG': 0, 'PY': 586, 'PE': 0, 'PF': 599, 'PL': 603, 'PT': 607, 'PR': 611,
                      'QA': 618, 'GB': 628, 'CF': 0, 'CZ': 0, 'CD': 0, 'DO': 0, 'RE': 0, 'RW': 675, 'RO': 670, 'WS': 687,
                      'AS': 0, 'BL': 0, 'KN': 0, 'SM': 697, 'SX': 0, 'MF': 0, 'PM': 0, 'VC': 705, 'SH': 0, 'LC': 0, 'VA': 0,
                      'ST': 0, 'SN': 728, 'RS': 0, 'SC': 731, 'SL': 735, 'SG': 741, 'SY': 0, 'SO': 748, 'LK': 750, 'SZ': 0,
                      'ZA': 756, 'SD': 759, 'SS': 0, 'SE': 764, 'CH': 767, 'SR': 770, 'SJ': 773, 'EH': 685, 'TH': 776,
                      'TW': 0, 'TJ': 0, 'TZ': 0, 'IO': 0, 'TF': 0, 'TL': 0, 'TG': 800, 'TK': 805, 'TO': 810, 'TT': 815,
                      'TM': 825, 'TR': 827, 'TV': 828, 'TN': 0, 'UA': 830, 'UG': 833, 'UY': 845, 'UZ': 847, 'VU': 551,
                      'VE': 850, 'VN': 855, 'WF': 875, 'YE': 880,  'DJ': 0, 'ZM': 890, 'ZW': 665}

        codeant = ''
        partnerant = 0
        reportlines = []
        dataline = {}
        paso = 0
        sorted_data = sorted(format_data, key=lambda row: (row['code'], row['partner_id']))
        print(sorted_data)
        for data in sorted_data:
            partner_id = data['partner_id']
            partner = self.env['res.partner'].search([('id', '=', partner_id)])
            print(partner.vat)
            if codeant != data['code'] or partnerant != partner_id:
                if paso == 1:
                    reportlines.append(dataline)
                paso = 0
                partnerant = partner.id
                codeant = data['code']

            if not partner.primer_nombre:
                primer_nombre = ''
            else:
                primer_nombre = partner.primer_nombre

            if not partner.segundo_nombre:
                segundo_nombre = ''
            else:
                segundo_nombre = partner.segundo_nombre

            if not partner.primer_apellido:
                primer_apellido = ''    
            else:
                primer_apellido = partner.primer_apellido

            if not partner.segundo_apellido:
                segundo_apellido = ''
            else:
                segundo_apellido = partner.segundo_apellido

            if not partner.name:
                razon_social = ''
            else:
                razon_social = partner.name

            if not partner.street:
                direccion = ''
            else:
                direccion = partner.street

            if not partner.fe_municipality_id:
                codigo_mcp = ''
                codigo_dpto = ''
            else:
                codigo_mcp = partner.fe_municipality_id.code
                codigo_dpto = codigo_mcp[:2]

            if not partner.country_id:
                codigo_pais = ''
            else:
                codigo_pais = cod_paises[partner.country_id.code]

            if not partner.email:
                correo = ''
            else:
                correo = partner.email

            if not partner.vat:
                vatid = ''
                dv = ''
            else:
                vatid = partner.vat.split('-')[0]
                if len(partner.vat.split('-')) > 1:
                    dv = partner.vat.split('-')[1]
                else:
                    dv = ''
            
            if partner.l10n_latam_identification_type_id:
                tipo_documento = switch_id[partner.l10n_latam_identification_type_id.l10n_co_document_code]

            if paso == 0:
                if self.report_type == '1001':
                    dataline = {
                        'Concepto': data['code'],
                        'Tipo de documento': tipo_documento,
                        'Número identificación': vatid,
                        'Primer apellido del informado': primer_apellido,
                        'Segundo apellido del informado': segundo_apellido,
                        'Primer nombre del informado': primer_nombre,
                        'Otros nombres del informado': segundo_nombre,
                        'Razón social informado': razon_social,
                        'Dirección': direccion,
                        'Código dpto': codigo_dpto,
                        'Código mcp': codigo_mcp,
                        'País de Residencia o domicilio': codigo_pais,
                        'Pago o abono en cuenta deducible': 0,
                        'Pago o abono en cuenta NO deducible': 0,
                        'IVA mayor valor del costo o gasto, deducible': 0,
                        'IVA mayor valor del costo o gasto no deducible': 0,
                        'Retención en la fuente practicada Renta': 0,
                        'Retención en la fuente asumida Renta': 0,
                        'Retención en la fuente practicada IVA Régimen común': 0,
                        'Retención en la fuente practicada IVA no domiciliados': 0,
                    }
                    paso = 1
                elif self.report_type == '1003':
                    dataline = {
                        'Concepto': data['code'],
                        'Tipo de documento': tipo_documento,
                        'Número identificación': vatid,
                        'DV': dv,
                        'Primer apellido del informado': primer_apellido,
                        'Segundo apellido del informado': segundo_apellido,
                        'Primer nombre del informado': primer_nombre,
                        'Otros nombres del informado': segundo_nombre,
                        'Razón social informado': razon_social,
                        'Dirección': direccion,
                        'Código del Departamento': codigo_dpto,
                        'Código del Municipio': codigo_mcp,
                        'Valor acumulado del pago o abono sujeto a Retención en la fuente': 0,
                        'Retención que le practicaron': 0,
                    }
                    paso = 1
                elif self.report_type == '1004':
                    dataline = {
                        'Concepto': data['code'],
                        'Tipo de documento del Tercero': tipo_documento,
                        'Número de Identificación del Tercero': vatid,
                        'Primer apellido': primer_apellido,
                        'Segundo apellido': segundo_apellido,
                        'Primer nombre': primer_nombre,
                        'Otros nombres': segundo_nombre,
                        'Razón Social': razon_social,
                        'Dirección': direccion,
                        'Código dpto': codigo_dpto,
                        'Código mcp': codigo_mcp,
                        'Código País': codigo_pais,
                        'Correo Electrónico': correo,
                        'Valor del descuento tributario total del año': 0,
                        'Valor del descuento tributario efectivamente solicitado en el año gravable': 0,
                    }
                    paso = 1
                elif self.report_type == '1005':
                    dataline = {
                        'Tipo de Documento': tipo_documento,
                        'Numero de identificación del informado': vatid,
                        'DV': dv,
                        'Primer apellido del informado': primer_apellido,
                        'Segundo apellido del informado': segundo_apellido,
                        'Primer nombre del informado': primer_nombre,
                        'Otros nombres del informado': segundo_nombre,
                        'Razón social informado': razon_social,
                        'Impuesto descontable': 0,
                        'IVA resultante por devoluciones en ventas anuladas rescindidas o resueltas': 0,
                    }
                    paso = 1
                elif self.report_type == '1006':
                    dataline = {
                        'Tipo de Documento': tipo_documento,
                        'Número identificación': vatid,
                        'DV': dv,
                        'Primer apellido del informado': primer_apellido,
                        'Segundo apellido del informado': segundo_apellido,
                        'Primer nombre del informado': primer_nombre,
                        'Otros nombres del informado': segundo_nombre,
                        'Razón social informado': razon_social,
                        'Impuesto generado': 0,
                        'IVA recuperado en devoluciones en compras anuladas rescindidas o resueltas': 0,
                        'Impuesto nacional al consumo': 0,
                    }
                    paso = 1
                elif self.report_type == '1007':
                    dataline = {
                        'Concepto': data['code'],
                        'Tipo de documento': tipo_documento,
                        'Número identificación del informado': vatid,
                        'Primer apellido del informado': primer_apellido,
                        'Segundo apellido del informado': segundo_apellido,
                        'Primer nombre del informado': primer_nombre,
                        'Otros nombres del informado': segundo_nombre,
                        'Razón social informado': razon_social,
                        'País de residencia o domicilio': codigo_pais,
                        'Ingresos brutos recibidos': 0,
                        'Devoluciones': 0,
                        'rebajas y descuentos': 0,
                    }
                    paso = 1
                elif self.report_type == '1008':
                    dataline = {
                        'Concepto': data['code'],
                        'Tipo de documento': tipo_documento,
                        'Número identificación': vatid,
                        'DV': dv,
                        'Primer apellido deudor': primer_apellido,
                        'Segundo apellido deudor': segundo_apellido,
                        'Primer nombre deudor': primer_nombre,
                        'Otros nombres deudor': segundo_nombre,
                        'Razón social deudor': razon_social,
                        'Dirección': direccion,
                        'Código dpto': codigo_dpto,
                        'Código mcp': codigo_mcp,
                        'País de residencia o domicilio': codigo_pais,
                        'Saldo cuentas por cobrar al 31-12': 0,
                    }
                    paso = 1
                elif self.report_type == '1009':
                    dataline = {
                        'Concepto': data['code'],
                        'Tipo de documento': tipo_documento,
                        'Número identificación': vatid,
                        'DV': dv,
                        'Primer apellido': primer_apellido,
                        'Segundo apellido': segundo_apellido,
                        'Primer nombre': primer_nombre,
                        'Otros nombres': segundo_nombre,
                        'Razón social': razon_social,
                        'Dirección': direccion,
                        'Código dpto': codigo_dpto,
                        'Código mcp': codigo_mcp,
                        'País de residencia o domicilio': codigo_pais,
                        'Saldo cuentas por pagar al 31-12': 0,
                    }
                    paso = 1
                elif self.report_type == '1010': # este no se usa
                    dataline = {
                        'Tipo de documento': tipo_documento,
                        'Número identificación': vatid,
                        'DV': dv,
                        'Primer apellido socio o accionista': primer_apellido,
                        'Segundo apellido socio o accionista': segundo_apellido,
                        'Primer nombre del socio o accionista': primer_nombre,
                        'Otros nombres del socio o accionista': segundo_nombre,
                        'Razón social': razon_social,
                        'Dirección': direccion,
                        'Código dpto': codigo_dpto,
                        'País de residencia o domicilio': codigo_pais,
                        'Valor patrimonial acciones o aportes al 31-12': 0,
                        'Porcentaje de participación': 0,
                        'Porcentaje de participación (posición decimal)': 0,
                    }
                    paso = 1
                elif self.report_type == '1647':  # en este se proporciona solo un terecero la segunda parte no se usa
                    dataline = {
                        'concepto': data['code'],
                        'Tipo de documento de quien se recibe el ingreso': tipo_documento,
                        'Número identificación de quien recibe el ingreso': vatid,
                        'DV': dv,
                        'Primer apellido de quien se recibe el ingreso': primer_apellido,
                        'Segundo apellido de quien se recibe el ingreso': segundo_apellido,
                        'Primer nombre de quien se recibe el ingreso': primer_nombre,
                        'Otros nombres de quien se recibe el ingreso': segundo_nombre,
                        'Razón social de quien se recibe el ingreso': razon_social,
                        'País de residencia o domicilio de quien se recibe el ingreso': codigo_pais,
                        'Valor total de la operación': 0,
                        'Valor ingreso reintegrado transferido distribuido al tercero': 0,
                        'Valor retención reintegrada transferida  distribuida al tercero': 0,
                        'Tipo de documento del tercero para quien se recibió el ingreso': tipo_documento,
                        'Identificación del tercero para quien se recibió el ingreso': partner.vat,
                        'Primer apellido del tercero para quien se recibió el ingreso': primer_apellido,
                        'Segundo apellido del tercero para quien se recibió el ingreso': segundo_apellido,
                        'Primer nombre del tercero para quien se recibió el ingreso': primer_nombre,
                        'Otros nombres del tercero para quien se recibió el ingreso': segundo_nombre,
                        'Razón social del tercero para quien se recibió el ingreso': razon_social,
                        'Dirección': direccion,
                        'Código dpto': codigo_dpto,
                        'Código mcp': codigo_mcp,
                        'País de residencia o domicilio': codigo_pais,
                    }
                    paso = 1
                elif self.report_type == '2275':
                    dataline = {
                        'concepto': data['code'],
                        'Tipo de documento del tercero': tipo_documento,
                        'Número identificación del tercero': vatid,
                        'Primer apellido del informado': primer_apellido,
                        'Segundo apellido del informado': segundo_apellido,
                        'Primer nombre del informado': primer_nombre,
                        'Otros nombres del informado': segundo_nombre,
                        'Razón social': razon_social,
                        'Dirección': direccion,
                        'Código dpto': codigo_dpto,
                        'Código mcp': codigo_mcp,
                        'Código País': codigo_pais,
                        'Correo electrónico': correo,
                        'Valor del ingreso no constitutivo de renta ni ganancia ocasional solicitado': 0,
                    }
                    paso = 1
                elif self.report_type == '2276':
                    dataline = {
                        'Entidad Informante': razon_social,
                        'Tipo de documento del beneficiario': tipo_documento,
                        'Número de Identificación del beneficiario': vatid,
                        'Primer Apellido del beneficiario': primer_apellido,
                        'Segundo Apellido del beneficiario': segundo_apellido,
                        'Primer Nombre del beneficiario': primer_nombre,
                        'Otros Nombres del beneficiario': segundo_nombre,
                        'Dirección del beneficiario': direccion,
                        'Departamento del beneficiario': codigo_dpto,
                        'Municipio del beneficiario': codigo_mcp,
                        'País del beneficiario': codigo_pais,
                        'Pagos por Salarios': 0,
                        'Pagos por emolumentos eclesiásticos': 0,
                        'Pagos por honorarios': 0,
                        'Pagos por servicios': 0,
                        'Pagos por comisiones': 0,
                        'Pagos por prestaciones sociales': 0,
                        'Pagos por viáticos': 0,
                        'Pagos por gastos de representación': 0,
                        'Pagos por compensaciones trabajo asociado cooperativo': 0,
                        'Otros pagos': 0,
                        'Cesantías e intereses de cesantías efectivamente pagadas, consignadas o reconocidas en el periodo': 0,
                        'Pensiones de Jubilación, vejez o invalidez': 0,
                        'Total Ingresos brutos de rentas de trabajo y pensión': 0,
                        'Aportes Obligatorios por Salud': 0,
                        'Aportes obligatorios a fondos de pensiones y solidaridad pensional y Aportes voluntarios al - RAIS': 0,
                        'Aportes voluntarios a fondos de pensiones voluntarias': 0,
                        'Aportes a cuentas AFC': 0,
                        'Aportes a cuentas AVC': 0,
                        'Valor de las retenciones en la fuente por pagos de rentas de trabajo o pensiones': 0,
                        'Pagos realizados con bonos electrónicos o de papel de servicio, cheques, tarjetas, vales, etc.	Apoyos económicos no reembolsables o condonados, entregados por el Estado o financiados con recursos públicos, para financiar programas educativos': 0,
                        'Pagos por alimentación mayores a 41 UVT': 0,
                        'Pagos por alimentación hasta a 41 UVT': 0,
                        'Identificación del fideicomiso o contrato': '',
                        'Tipo documento participante en contrato de colaboración': '',
                        'Identificación participante en contrato colaboración': '',
                    }
                    paso = 1
            if paso == 1:
                keystr = columnas[data['column_number'] - 1]
                if data['calculation_type'] == 'sumd':
                    if dataline[keystr]:
                        if dataline[keystr]> 0:
                            dataline[keystr] += abs(data['debit'])
                        else:
                            dataline[keystr] = abs(data['debit'])
                    else:
                        dataline[keystr] = abs(data['debit'])
                elif data['calculation_type'] == 'sumc':
                    if dataline[keystr]:
                        if dataline[keystr]> 0:
                            dataline[keystr] += abs(data['credit'])
                        else:
                            dataline[keystr] = abs(data['credit'])
                    else:
                        dataline[keystr] = abs(data['credit'])
                else:
                    if dataline[keystr]:
                        if dataline[keystr]> 0:
                            dataline[keystr] += abs(data['balance'])
                        else:
                            dataline[keystr] = abs(data['balance'])
                    else:
                        dataline[keystr] = abs(data['balance'])

        if paso == 1:
            reportlines.append(dataline)

        pt_exogena_report = self.env['pt.exogena.report']
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'lines': reportlines,
            'type': self.report_type,
            'columns': columnas,
        }

        return pt_exogena_report.show_report(data)
        #return self.env.ref('pt_exogena.action_exogena_xlsx_report').report_action(self, data=data)


class ExogenaReport(models.TransientModel):
    _name = 'pt.exogena.report'
    _description = 'Exogena Report'

    name = fields.Char('Nombre', default='Exogena')
    col_1 = fields.Char('Columna 1')
    col_2 = fields.Char('Columna 2')
    col_3 = fields.Char('Columna 3')
    col_4 = fields.Char('Columna 4')
    col_5 = fields.Char('Columna 5')
    col_6 = fields.Char('Columna 6')
    col_7 = fields.Char('Columna 7')
    col_8 = fields.Char('Columna 8')
    col_9 = fields.Char('Columna 9')
    col_10 = fields.Char('Columna 10')
    col_11 = fields.Char('Columna 11')
    col_12 = fields.Char('Columna 12')
    col_13 = fields.Char('Columna 13')
    col_14 = fields.Char('Columna 14')
    col_15 = fields.Char('Columna 15')
    col_16 = fields.Char('Columna 16')
    col_17 = fields.Char('Columna 17')
    col_18 = fields.Char('Columna 18')
    col_19 = fields.Char('Columna 19')
    col_20 = fields.Char('Columna 20')
    col_21 = fields.Char('Columna 21')
    col_22 = fields.Char('Columna 22')
    col_23 = fields.Char('Columna 23')
    col_24 = fields.Char('Columna 24')
    col_25 = fields.Char('Columna 25')
    col_26 = fields.Char('Columna 26')
    col_27 = fields.Char('Columna 27')
    col_28 = fields.Char('Columna 28')
    col_29 = fields.Char('Columna 29')
    col_30 = fields.Char('Columna 30')
    col_31 = fields.Char('Columna 31')
    col_32 = fields.Char('Columna 32')
    col_33 = fields.Char('Columna 33')
    col_34 = fields.Char('Columna 34')
    col_35 = fields.Char('Columna 35')
    col_36 = fields.Char('Columna 36')
    col_37 = fields.Char('Columna 37')
    col_38 = fields.Char('Columna 38')
    col_39 = fields.Char('Columna 39')
    col_40 = fields.Char('Columna 40')

    def clean_data(self):
        self.env["pt.exogena.report"].search([]).unlink()
        return True

    def show_report(self, data):
        self.clean_data()
        columns = data["columns"]
        lineas = data["lines"]

        data_reg = {}
        col_name = 'col_'
        col_counter = 1
        for column in columns:
            data_reg[col_name + str(col_counter)] = column
            col_counter += 1

        print(data_reg)
        self.env["pt.exogena.report"].create(data_reg)

        for line in lineas:
            line_reg = {}
            col_counter = 1
            for column in columns:
                line_reg[col_name + str(col_counter)] = line[column]
                col_counter += 1
            print(line_reg)
            self.env["pt.exogena.report"].create(line_reg)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pt.exogena.report',
            'view_mode': 'tree',
            'target': 'current'
        }
