# -*- coding: utf-8 -*-
from odoo import models, api, _, fields, exceptions
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT, _logger
from datetime import timedelta, date, datetime
import requests, time, base64, json, logging
from http.client import responses as res


class FeMfConfiguration(models.Model):
    _name = "fe.mf.config"
    _description = "Fe with Mis Facturas"

    name = fields.Char(compute="compute_name", store=True)
    user = fields.Char('User')
    password = fields.Char('Password')
    url_web_service = fields.Char('Route')
    test = fields.Boolean('Test')
    test_mode = fields.Boolean('Test Mode')
    test_user = fields.Char('User')
    test_password = fields.Char('Password')
    test_url_web_service = fields.Char('Route')

    @api.constrains
    def one_configuration(self):
        if self.env['fe.mf.config'].search([('id', '!=', self.id)]):
            raise exceptions.ValidationError("Solo pude tener una configuración")

    @api.depends('user')
    def compute_name(self):
        self.name = self.user

    @api.model
    def create(self, vals_list):
        test_mode = vals_list['test_mode'] if 'test_mode' in vals_list else self.test_mode
        if test_mode:
           vals_list['test'] = self.env['fe.mf.methods'].login(vals_list['test_user'], vals_list['test_password'],vals_list['test_url_web_service'])
        else:
           vals_list['test'] = self.env['fe.mf.methods'].login(vals_list['user'], vals_list['password'],vals_list['url_web_service'])
        return super(FeMfConfiguration, self).create(vals_list)

    def write(self, vals_list):
        user = vals_list['user'] if 'user' in vals_list else self.user
        password = vals_list['password'] if 'password' in vals_list else self.password
        url = vals_list['url_web_service'] if 'url_web_service' in vals_list else self.url_web_service
        test_mode = vals_list['test_mode'] if 'test_mode' in vals_list else self.test_mode
        if test_mode:
            user = vals_list['test_user'] if 'test_user' in vals_list else self.test_user
            password = vals_list['test_password'] if 'test_password' in vals_list else self.test_password
            url = vals_list['test_url_web_service'] if 'test_url_web_service' in vals_list else self.test_url_web_service
        vals_list['test'] = self.env['fe.mf.methods'].login(user, password, url)
        return super(FeMfConfiguration, self).write(vals_list)

    @api.onchange('user', 'password', 'url_web_service')
    def disable_test(self):
        self.test = False


class FeMfLoginToken(models.TransientModel):
    _name = "fe.mf.login.token"
    _description = "Get token"

    date = fields.Date('Date')
    token = fields.Char('Token')
    # To-Do Agregar constrains de fecha


class FeMfMethods(models.AbstractModel):
    _name = "fe.mf.methods"
    _description = "Metodos para la interfaz del cliente API"

    def login(self, user="", password="", url=""):
        """
        Función para iniciar sesión en el servicio de Mis Facturas
        @param user: Usuario con el cual debe iniciar sesión
        @param password: Contraseña con la cual debe iniciar sesión
        @param url: Base de la url (cambia si es produccion o si es pruebas) donde debe enviar la paeticion de inicio de sesión
        @return: Booleano que representa eel estado del inicio de sesión
        """
        if user is " ":
            data = self.env['fe.mf.config'].search([])
            if not data:
                raise exceptions.ValidationError("Configure los datos de conexion al servicio de Mis Facturas")
            user = data.user
            password = data.password
            url = data.url
        today = date.today()
        url_service = str(url + "login/?username=" + user + "&password=" + password)
        payload = {}
        files = {}
        headers = {}
        response = requests.request("POST", url_service, headers=headers, data=payload, files=files)
        if response.status_code is 200:
            login = self.env['fe.mf.login.token'].search([('date', '=', today)])
            if not login:
                self.env['fe.mf.login.token'].create({
                    'date': today,
                    'token': str("misfacturas " + response.content.decode('utf8').split('"')[1])
                })
            return True
        else:
            raise exceptions.ValidationError("Error al conectar, usuario o contraseña incorrecta.")
            return False

    def _get_token(self, config):
        """
        Función para obtener el token de día, si no existe crea uno nuevo.
        @param config: Usuario, Contraseña, Url del servicio (sengun prueba o producción)
        @return:
        """
        today = date.today()
        env_token = self.env['fe.mf.login.token'].search([('date', '=', today)])
        if env_token:
            return env_token.token
        else:
            user = config.user
            password = config.password
            url_web_service = config.url_web_service
            if config.test_mode:
                user = config.test_user
                password = config.test_password
                url_web_service = config.test_url_web_service

            self.login(user, password, url_web_service)
            return self._get_token(config)

    def _get_parameters_connection(self):
        """
        Función para obtener token de acceso y url
        @return: Diccionario con el token de acceso y la url base del servicio
        """
        config = self.env['fe.mf.config'].search([])
        url_web_service = config.url_web_service
        if config.test_mode:
            url_web_service = config.test_url_web_service
        return {'token': self._get_token(config), 'url': url_web_service}

    def _get_parameters_settings(self):
        """
        Función para obtener parametros del res.config.settings
        @return: Diccionario con el token de acceso y la url base del servicio
        """
        parameter = self.env['ir.config_parameter'].sudo()
        fe_own_gr = parameter.get_param('res.config.settings.fe_own_gr')
        if fe_own_gr:
            fe_own_gr = "true"
        else:
            fe_own_gr = "false"
        return {'fe_own_gr': fe_own_gr}

    def load_invoice_line_data_to_json(self, template_id, posted_document):
        """
        Función que permite construir una lista de diccionaros con las lineas
        (productos e impuestos respectivos) de una factura o nota credito
        @param template_id: Plantilla según cual se construye el cuerpo de del json
        @param posted_document: Factura
        @return: Lista de diccionaros con las lineas
        """
        lines = []
        if template_id == 73:
            for line in posted_document.invoice_line_ids:
                if not line.display_type:
                    taxes = []
                    move_tax_line = self.env['account.move.taxes.line'].search(
                        [('move_line_id', '=', line.id), ('move_id', '=', line.move_id.id)])
                    line_total_taxes = 0
                    for tax in move_tax_line:
                        if not tax.tax_type_id.type == '07':
                            if not tax.tax_type_id.type == '05':
                                if not tax.tax_type_id.code == 'NA':
                                    tax_information = {
                                        "Id": tax.tax_type_id.type,
                                        "TaxEvidenceIndicator": "false" if tax.tax_type_id.operation == "S" else "true",
                                        "TaxableAmount": tax.base,
                                        "TaxAmount": abs(tax.amount),
                                        "Percent": abs(tax.percent),
                                        "BaseUnitMeasure": 0,
                                        "PerUnitAmount": 0
                                    }
                                    if tax_information['TaxEvidenceIndicator']:
                                        line_total_taxes += tax.amount
                                    taxes.append(tax_information)

                    allowance = []
                    discount_prod = 0
                    original_price = line.quantity * line.price_unit
                    original_price_total = str("{:,}".format(round(original_price,2)).replace(',', 'x').replace('.', ',').replace('x', '.'))
                    if line.discount > 0:
                        discount_prod = (original_price * line.discount)/100
                        allowance.append({
                            "Id": "02",
                            "ChargeIndicator": "false",
                            "AllowanceChargeReason": "DESCUENTO",
                            "MultiplierFactorNumeric": line.discount,
                            "Amount": discount_prod,
                            "BaseAmount": original_price
                        })
                    product = {
                        "ItemReference": line.product_id.default_code,
                        "Name": line.product_id.name,
                        "SSIdentification": "",
                        "SSDescription": "",
                        "SSAuthorizationID": "",
                        "SSCodigoPrestador": "",
                        "Quatity": line.quantity,
                        "Price": line.price_unit,
                        "LineAllowanceTotal": discount_prod,
                        "LineChargeTotal": 0.0,
                        "LineTotalTaxes": line_total_taxes,
                        "LineTotal": line.price_subtotal + line_total_taxes,
                        "LineExtensionAmount": line.price_subtotal,
                        "MeasureUnitCode": line.product_id.uom_id.dian_code.key_dian,
                        "FreeOFChargeIndicator": "false",
                        "Equals10Percent": "false",
                        "AdditionalReference": [],
                        "Nota": "",
                        "AdditionalProperty": [
                            {"Name": "Tot Linea",
                             "Value": '$ '+original_price_total
                             },
                        ],
                        "TaxesInformation": taxes,
                        "AllowanceCharge": []
                    }
                    lines.append(product)


        if template_id == 217:

            cont_line = len(posted_document.invoice_line_ids)
            for line in posted_document.invoice_line_ids:
                if not line.display_type:
                    taxes = []
                    move_tax_line = self.env['account.move.taxes.line'].search(
                        [('move_line_id', '=', line.id), ('move_id', '=', line.move_id.id)])
                    line_total_taxes = 0
                    line_tot_producto = 0
                    line_flete = round(
                        (posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop / posted_document.trm),
                        2)
                    line_otros = round(
                        (posted_document.x_studio_field_3lEMz.x_studio_otros_cop / posted_document.trm),
                        2)
                    line_seguro = posted_document.x_studio_field_3lEMz.x_studio_monto_seguro_usd_1
                    line_tot_otros = (line_flete + line_otros + line_seguro) / cont_line
                    line_tot_producto = line.price_subtotal - line_tot_otros

                    precio_un_producto = round((line_tot_producto / line.quantity),2)

                    for tax in move_tax_line:
                        if not tax.tax_type_id.type == '07':
                            if not tax.tax_type_id.type == '05':
                                if not tax.tax_type_id.code == 'NA':
                                    tax_information = {
                                        "Id": tax.tax_type_id.type,
                                        "TaxEvidenceIndicator": "false" if tax.tax_type_id.operation == "S" else "true",
                                        "TaxableAmount": tax.base,
                                        "TaxAmount": abs(tax.amount),
                                        "Percent": abs(tax.percent),
                                        "BaseUnitMeasure": 0,
                                        "PerUnitAmount": 0
                                    }
                                    if tax_information['TaxEvidenceIndicator']:
                                        line_total_taxes += tax.amount
                                    taxes.append(tax_information)

                    product = {
                        "ItemReference": line.product_id.default_code,
                        "Name": line.product_id.name,
                        "SSIdentification": "",
                        "SSDescription": "",
                        "SSAuthorizationID": "",
                        "SSCodigoPrestador": "",
                        "Quatity": line.quantity,
#                      "Price": line.price_unit,

                        "Price": precio_un_producto,
                        "LineAllowanceTotal": 0,
                        "LineChargeTotal": 0.0,
                        "LineTotalTaxes": line_total_taxes,
                        "LineTotal": (line_tot_producto - line.discount) + line_total_taxes,
#                        "LineTotal": (line.price_subtotal - line.discount) + line_total_taxes,
                        "BrandName": "Pacifico Snacks",
                        "ModelName": "Snacks",
#                        "LineExtensionAmount": line.price_subtotal - line.discount,
                        "LineExtensionAmount": line_tot_producto - line.discount,
                        "MeasureUnitCode": line.product_id.uom_id.dian_code.key_dian,
                        "FreeOFChargeIndicator": "false",
                        "Equals10Percent": "false",
                        "AdditionalReference": [],
                        "Nota": "",
                        "AdditionalProperty": [{
                            "Name": "CODIGO CLIENTE / CUSTOMER#",
                            "Value": posted_document.partner_id.cod_customer},
                            {"Name": "ORDEN DE COMPRA / P.O.#",
                             "Value": posted_document.x_studio_field_3lEMz.x_studio_po_},
                            {"Name": "POS ARANCELARIA / CUSTOMS TARIFF",
                             "Value": line.product_id.x_studio_posicion_arancelaria
                             }],
                        "TaxesInformation": taxes,
                        "AllowanceCharge": []
                    }
                    lines.append(product)


        if template_id == 91:
            for line in posted_document.invoice_line_ids:
                if not line.display_type:
                    taxes = []
                    move_tax_line = self.env['account.move.taxes.line'].search(
                        [('move_line_id', '=', line.id), ('move_id', '=', line.move_id.id)])
                    line_total_taxes = 0
                    for tax in move_tax_line:
                        if not tax.tax_type_id.type == '07':
                            tax_information = {
                                "Id": tax.tax_type_id.type,
                                "TaxEvidenceIndicator": "false" if tax.tax_type_id.operation == "S" else "true",
                                "TaxableAmount": tax.base,
                                "TaxAmount": abs(tax.amount),
                                "Percent": abs(tax.percent),
                                "BaseUnitMeasure": 0,
                                "PerUnitAmount": 0
                            }
                            if tax_information['TaxEvidenceIndicator']:
                                line_total_taxes += tax.amount
                            taxes.append(tax_information)

                    product = {
                        "ItemReference": line.product_id.default_code,
                        "Name": line.product_id.name,
                        "SSIdentification": "",
                        "SSDescription": "",
                        "SSAuthorizationID": "",
                        "SSCodigoPrestador": "",
                        "Quatity": line.quantity,
                        "Price": line.price_unit,
                        "LineAllowanceTotal": 0,
                        "LineChargeTotal": 0.0,
                        "LineTotalTaxes": line_total_taxes,
                        "LineTotal": (line.price_subtotal - line.discount) + line_total_taxes,
                        "BrandName": "Pacifico Snacks",
                        "ModelName": "Snacks",
                        "LineExtensionAmount": line.price_subtotal - line.discount,
                        "MeasureUnitCode": line.product_id.uom_id.dian_code.key_dian,
                        "FreeOFChargeIndicator": "false",
                        "AdditionalReference": [],
                        "Nota": "",
                        "AdditionalProperty": [{
                            "Name": "CODIGO CLIENTE / CUSTOMER#",
                            "Value": posted_document.partner_id.cod_customer},
                            {"Name": "ORDEN DE COMPRA",
                             "Value": posted_document.x_studio_field_3lEMz.x_studio_po_},
                            {"Name": "POS ARANCELARIA / CUSTOMS TARIFF",
                             "Value": line.product_id.x_studio_posicion_arancelaria
                        }],
                        "TaxesInformation": taxes,
                        "AllowanceCharge": []
                    }
                    lines.append(product)

        return lines

    def load_invoice_total_tax_to_json(self, template_id, posted_document):
        """
        Función que permite construir una lista de diccionaros con los totales de
        impuestos de la factura o nota credito
        @param template_id: Plantilla según cual se construye el cuerpo de del json
        @param posted_document: Factura
        @return: Lista de diccionaros con los totales de impuestos
        """
        lines = []
        if template_id == 73:
            move_tax = self.env['account.move.taxes'].search([('move_id', '=', posted_document.id)])
            for tax in move_tax:
                if not tax.tax_type_id.code == 'NA':
                    if tax.tax_type_id.type == '05':
                        percent_tax = 15
                    else:
                        percent_tax = abs(tax.percent)
                    lines.append({
                        "Id": tax.tax_type_id.type,
                        "TaxEvidenceIndicator": "false" if tax.tax_type_id.operation == "S" else "true",
                        "TaxableAmount": tax.base,
                        "TaxAmount": abs(tax.amount),
                        "Percent": percent_tax,
                        "BaseUnitMeasure": 0,
                        "PerUnitAmount": 0
                    })
                

        if template_id == 217:
            move_tax = self.env['account.move.taxes'].search([('move_id', '=', posted_document.id)])
            for tax in move_tax:
                if not tax.tax_type_id.code == 'NA':
                    if tax.tax_type_id.type == '05':
                        percent_tax = 15
                    else:
                        percent_tax = abs(tax.percent)
                    lines.append({
                        "Id": tax.tax_type_id.type,
                        "TaxEvidenceIndicator": "false" if tax.tax_type_id.operation == "S" else "true",
                        "TaxableAmount": tax.base,
                        "TaxAmount": abs(tax.amount),
                        "Percent": percent_tax,
                        "BaseUnitMeasure": 0,
                        "PerUnitAmount": 0
                    })

        if template_id == 91:
            move_tax = self.env['account.move.taxes'].search([('move_id', '=', posted_document.id)])
            for tax in move_tax:
                lines.append({
                    "Id": tax.tax_type_id.type,
                    "TaxEvidenceIndicator": "false" if tax.tax_type_id.operation == "S" else "true",
                    "TaxableAmount": tax.base,
                    "TaxAmount": abs(tax.amount),
                    "Percent": abs(tax.percent),
                    "BaseUnitMeasure": 0,
                    "PerUnitAmount": 0
                })
        return lines

    def load_ed_data_to_json(self, template_id, posted_document, gr, documents):
        """
        Función que permite construir un diccionario a partir de una factura o nota credito para luego
        ser enviada como json al servicio de Mis Facturas
        @param gr: Reprentación grafica
        @param template_id: Plantilla según cual se construye el cuerpo de del json
        @param posted_document: Factura
        @return: Diccionario con los valores de una factura
        """
        data_json = {}
        if template_id == 73:
            tax_total = self.load_invoice_total_tax_to_json(template_id, posted_document)
            tax_exclusive_amount = 0
            tax_inclusive_amount = 0
            for tax in tax_total:
                if tax['TaxEvidenceIndicator'] == 'false':
                    tax_exclusive_amount += tax['TaxableAmount']
                    tax_inclusive_amount += tax['TaxAmount']

            data_json = {
                "CustomerInformation": {
                    "IdentificationType": posted_document.partner_id.document_type.key_dian,
                    "Identification": int(posted_document.partner_id.vat),
                    "DV": int(posted_document.partner_id.verification_code),
                    "RegistrationName": posted_document.partner_id.display_name,
                    "CountryCode": posted_document.partner_id.country_id.code,
                    "CountryName": posted_document.partner_id.country_id.name,
                    "SubdivisionCode": int(posted_document.partner_id.state_id.key_dian),
                    "SubdivisionName": posted_document.partner_id.state_id.name,
                    "CityCode": posted_document.partner_id.city_id.key_dian if posted_document.partner_id.country_id.code == "CO" else "",
                    "CityName": posted_document.partner_id.city_id.name,
                    "AddressLine": posted_document.partner_id.street,
                    "Telephone": posted_document.partner_id.phone,
                    "Email": posted_document.partner_id.email,
                    "CustomerCode": posted_document.partner_id.id,
                    "AdditionalAccountID": int(posted_document.partner_id.person_type.key_dian),
                    "TaxLevelCodeListName": int(
                        posted_document.partner_id.property_account_position_id.key_dian.key_dian),
                    "PostalZone": int(posted_document.partner_id.zip),
                    "TaxSchemeCode": "01" if posted_document.partner_id.property_account_position_id.key_dian.key_dian == '48' else 'ZY',
                    "TaxSchemeName": "IVA" if posted_document.partner_id.property_account_position_id.key_dian.key_dian == '48' else 'No causa',
                    "FiscalResponsabilities": self.fiscal_responsabilities(posted_document),
                    "PartecipationPercent": 100,
                    "AdditionalCustomer": []
                },
                "InvoiceGeneralInformation": {
                    "InvoiceAuthorizationNumber": posted_document.journal_id.invoice_resolution.resolution,
                    "PreinvoiceNumber": posted_document.number,
                    "InvoiceNumber": posted_document.number,
                    "IssueDate": str(posted_document.invoice_date),
                    "DaysOff": posted_document.invoice_payment_term_id.line_ids.days,
                    "Currency": posted_document.currency_id.name,
                    "ExchangeRate": float(posted_document.exchange_rate),
                    "ExchangeRateDate": str(posted_document.invoice_date),
                    "CustomizationID": "",
                    "SchemeID": "",
                    "SalesPerson": posted_document.invoice_user_id.name,
                    "Note": "",
                    "ExternalGR": 'false',
                    "InvoiceDueDate": (posted_document.date + timedelta(
                        days=posted_document.invoice_payment_term_id.line_ids.days)).strftime("%Y-%m-%d"),
                    "StartDateTime": "0001-01-01T00:00:00",
                    "EndDateTime": "0001-01-01T00:00:00"
                },
                "Delivery": {
                    "AddressLine": "",
                    "CityCode": "",
                    "CityName": "",
                    "ContactPerson": "",
                    "CountryCode": "",
                    "CountryName": "",
                    "DeliveryCompany": "",
                    "DeliveryDate": "",
                    "SubdivisionCode": "",
                    "SubdivisionName": ""
                },
                "AdditionalDocuments": {
                    "OrderReference": "",
                    "OrderReferenceIssueDate": "0001-01-01T00:00:00",
                    "DespatchDocumentReference": "",
                    "DespatchDocumentIssueDate": "0001-01-01T00:00:00",
                    "ReceiptDocumentReference": "",
                    "ReceiptDocumentIssueDate": "0001-01-01T00:00:00",
                    "AdditionalDocument": []
                },
                "AdditionalDocumentReceipt": [],
                "AdditionalProperty": [],
                "PaymentSummary": {
                    "PaymentType": int(posted_document.payment_type_1),
                    "PaymentMeans": int(posted_document.payment_method.key_dian),
                    "PaymentNote": ""
                },
                "ItemInformation": self.load_invoice_line_data_to_json(template_id, posted_document),
                "InvoiceTaxTotal": tax_total,
                "InvoiceAllowanceCharge": [],
                "InvoiceTotal": {
                    "LineExtensionAmount": posted_document.amount_untaxed,
                    "TaxExclusiveAmount": tax_exclusive_amount,
                    "TaxInclusiveAmount": posted_document.amount_untaxed + tax_inclusive_amount,
                    "AllowanceTotalAmount": 0.0,
                    "ChargeTotalAmount": 0.0,
                    "PrePaidAmount": 0,  # posted_document.invoice_payments_widget,
                    "PayableAmount": posted_document.amount_untaxed + tax_inclusive_amount
                    # Deseable calcular los 4 campos
                },
                "Documents": documents
            }

        if template_id == 217:
                line_product = posted_document.invoice_line_ids
                total_peso_bruto = 0
                total_caja = 0
                total_unidades = 0
                for p in line_product:
                    total_peso_bruto += round(int(p.quantity)/p.product_id.x_studio_unidad_de_empaque) * p.product_id.x_studio_peso_bruto
                    total_caja += int(int(p.quantity)/p.product_id.x_studio_unidad_de_empaque)
                    total_unidades += int(p.quantity)

                total_peso_neto = round((total_peso_bruto - (total_caja * 0.75)))
                tax_total = self.load_invoice_total_tax_to_json(template_id, posted_document)
                tax_exclusive_amount = 0
                tax_inclusive_amount = 0
                number = posted_document.amount_untaxed + tax_inclusive_amount
                numbertotext = self.env['number.to.text'].to_word(number, 'USD')
# Determina si el cliente tiene otros contactos campo parent_id
                if posted_document.partner_id.parent_id:
                    IdentificationType = posted_document.partner_id.parent_id.document_type.key_dian
                    Identification = int(posted_document.partner_id.parent_id.vat)
                    DV = int(posted_document.partner_id.parent_id.verification_code)
                    RegistrationName = posted_document.partner_id.parent_id.display_name
                    CountryCode = posted_document.partner_id.parent_id.country_id.code
                    CountryName = posted_document.partner_id.parent_id.country_id.name
                    SubdivisionCode = int(posted_document.partner_id.parent_id.state_id.key_dian)
                    SubdivisionName = posted_document.partner_id.parent_id.state_id.code
                    CityCode = posted_document.partner_id.parent_id.city_id.key_dian if posted_document.partner_id.country_id.code == "CO" else ""
                    CityName = posted_document.partner_id.parent_id.city_id.name
#                    AddressLine = posted_document.partner_id.street
                    AddressLine = str(posted_document.partner_id.parent_id.street)
#                    AddressLine = str(posted_document.partner_id.parent_id.street) + " " + str(posted_document.partner_id.parent_id.state_id.code) + " " + str(posted_document.partner_id.parent_id.zip)
                    Telephone = posted_document.partner_id.parent_id.phone
                    Email = posted_document.partner_id.parent_id.email
                    CustomerCode = posted_document.partner_id.parent_id.id
                    AdditionalAccountID = int(posted_document.partner_id.parent_id.person_type.key_dian)
                    TaxLevelCodeListName = int(posted_document.partner_id.parent_id.property_account_position_id.key_dian.key_dian)
#                    PostalZone = " "
                    PostalZone = int(posted_document.partner_id.parent_id.zip)
                    TaxSchemeCode = "01" if posted_document.partner_id.parent_id.property_account_position_id.key_dian.key_dian == '48' else 'ZY'
                    TaxSchemeName = "IVA" if posted_document.partner_id.parent_id.property_account_position_id.key_dian == '48' else 'No causa'

                else:
                    IdentificationType = posted_document.partner_id.document_type.key_dian
                    Identification = int(posted_document.partner_id.vat)
                    DV = int(posted_document.partner_id.verification_code)
                    RegistrationName = posted_document.partner_id.display_name
                    CountryCode = posted_document.partner_id.country_id.code
                    CountryName = posted_document.partner_id.country_id.name
                    SubdivisionCode = int(posted_document.partner_id.state_id.key_dian)
                    SubdivisionName = posted_document.partner_id.state_id.code
                    CityCode = posted_document.partner_id.city_id.key_dian if posted_document.partner_id.country_id.code == "CO" else ""
                    CityName = posted_document.partner_id.city_id.name

                    AddressLine = str(posted_document.partner_id.parent_id.street)
#                  AddressLine = str(posted_document.partner_id.parent_id.street) + " " + str(posted_document.partner_id.parent_id.state_id.code) + " " + str(posted_document.partner_id.parent_id.zip)
                    Telephone = posted_document.partner_id.phone
                    Email = posted_document.partner_id.email
                    CustomerCode = posted_document.partner_id.id
                    AdditionalAccountID = int(posted_document.partner_id.person_type.key_dian)
                    TaxLevelCodeListName = int(posted_document.partner_id.property_account_position_id.key_dian.key_dian)
                    PostalZone = int(posted_document.partner_id.zip)
#                    PostalZone = " "
                    TaxSchemeCode = "01" if posted_document.partner_id.property_account_position_id.key_dian.key_dian == '48' else 'ZY'
                    TaxSchemeName = "IVA" if posted_document.partner_id.property_account_position_id.key_dian == '48' else 'No causa'

                line_tot_flete = round((posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop / posted_document.trm),2)
                line_tot_seguro = posted_document.x_studio_field_3lEMz.x_studio_monto_seguro_usd_1
                line_tot_otros = round((posted_document.x_studio_field_3lEMz.x_studio_otros_cop / posted_document.trm),2)
                line_tot_cargos = line_tot_flete + line_tot_seguro + line_tot_otros

#                line_sub_total_tax = line_sub_total
                line_sub_total_tax = posted_document.amount_untaxed - line_tot_flete - line_tot_seguro - line_tot_otros
                for tax in tax_total:
                    if tax['TaxEvidenceIndicator'] == 'false':
                        tax_exclusive_amount += tax['TaxableAmount']
                        tax_inclusive_amount += tax['TaxAmount']
                data_json = {
                    "CustomerInformation": {
                        "IdentificationType": IdentificationType,
                        "Identification": Identification,
                        "DV": DV,
                        "RegistrationName": RegistrationName,
                        "CountryCode": CountryCode,
                        "CountryName": CountryName,
                        "SubdivisionCode": SubdivisionCode,
                        "SubdivisionName": SubdivisionName,
                        "CityCode": CityCode,
                        "CityName": CityName,
                        "AddressLine": AddressLine,
                        "Telephone": Telephone,
                        "Email": Email,
                        "CustomerCode": CustomerCode,
                        "AdditionalAccountID": AdditionalAccountID,
                        "TaxLevelCodeListName": TaxLevelCodeListName,
                        "PostalZone": PostalZone,
                        "TaxSchemeCode": TaxSchemeCode,
                        "TaxSchemeName": TaxSchemeName,
                        "FiscalResponsabilities": self.fiscal_responsabilities(posted_document),
                        "PartecipationPercent": 100,
                        "AdditionalCustomer": [],
                        "DoNotToSentEmailBody": 'false',
                    },
                    "InvoiceGeneralInformation": {
                        "InvoiceAuthorizationNumber": posted_document.journal_id.invoice_resolution.resolution,
                        "PreinvoiceNumber": posted_document.number,
                        "InvoiceNumber": posted_document.number,
                        "IssueDate": str(posted_document.invoice_date),
#                        "DaysOff": posted_document.invoice_payment_term_id.line_ids.days,
                        "DaysOff": posted_document.invoice_payment_term_id.name,
                        "Currency": posted_document.currency_id.name,
                        "ExchangeRate": float(posted_document.trm),
                        "ExchangeRateDate": str(posted_document.invoice_date),
                        "CustomizationID": "",
                        "SchemeID": "",
                        "SalesPerson": posted_document.invoice_user_id.name,
                        "Note": 'INGREDIENTS : ' + str(
                            posted_document.partner_id.x_studio_ingredientes) + ' / PRODUCT OF COLOMBIA ' + ' / FDA REGISTRATION NUMBER: 12218565886 ' + ' / NET WEIGHT: ' + str(total_peso_neto) + 'Kg / GROSS WEIGHT: ' + str(round(total_peso_bruto)) + 'Kg  / TOTAL UNITS: ' + str(total_unidades) + ' / TOTAL CASES: ' + str(total_caja) + ' CONTAINER NUMBER: ' + str(
                            posted_document.x_studio_field_3lEMz.x_studio_contenedor_asignado) + ' / ' + str(
                            posted_document.x_studio_field_3lEMz.x_studio_descripcion_contenedor_1) + ' / NON PALLETIZED CARGO / ' + 'GOODS TO BE RESOLD UNDER ' + RegistrationName + '  TRADE NAME ',
                        "ExternalGR": 'false',
                        "InvoiceDueDate": (posted_document.x_studio_fecha_de_vencimiento).strftime("%Y-%m-%d") ,
                        "StartDateTime": "0001-01-01T00:00:00",
                        "EndDateTime": "0001-01-01T00:00:00"
                    },
                    "Delivery": {
#                        "AddressLine": str(posted_document.partner_id.street) + " " + str(posted_document.partner_id.state_id.code) + " " + str(posted_document.partner_id.zip),
                        "AddressLine": str(posted_document.partner_id.street_14),
                        "CityCode": "",
                        "CityName": str(posted_document.partner_id.city_id.name),
                        "ContactPerson": "",
                        "CountryCode": str(posted_document.partner_id.country_id.code),
                        "CountryName": str(posted_document.partner_id.country_id.name),
                        "DeliveryDate": str(posted_document.invoice_date),
                        "DeliveryCompany": "",
                        "LossRiskResponsibilityCode": str(
                            posted_document.x_studio_field_3lEMz.x_studio_incoterm_1),
#                           + str(posted_document.x_studio_field_3lEMz.x_studio_puerto_de_origen),
                        "SubdivisionCode": "",
                        "SubdivisionName": str(posted_document.partner_id.state_id.name),
                        "IdentificationConveyor": "",
                        "DVConveyor": ""
                    },
                    "AdditionalDocuments": {
                        "OrderReference": "",
                        "OrderReferenceIssueDate": "0001-01-01T00:00:00",
                        "DespatchDocumentReference": "",
#                        "DespatchDocumentReference": 'DOC. INTERNO:' + str(posted_document.invoice_origin),
                        "DespatchDocumentIssueDate": "0001-01-01T00:00:00",
                        "ReceiptDocumentReference": "",
                        "ReceiptDocumentIssueDate": "0001-01-01T00:00:00",
                        "AdditionalDocument": []
                    },
                    "AdditionalDocumentReceipt": [],
                    "AdditionalProperty": [
                        {"Name": "Puerto Origen",
                         "Value": posted_document.x_studio_field_3lEMz.x_studio_puerto_de_origen},
                        {"Name": "TEL/PHO:",
                         "Value": posted_document.partner_id.phone},
                        {"Name": "Doc. Interno",
                         "Value": 'DOC. INTERNO:' + str(posted_document.invoice_origin)
                        },
                        {"Name": "UbicationCustomer",
                         "Value": str(posted_document.partner_id.parent_id.city_id.name) + " " + str(
                             posted_document.partner_id.parent_id.state_id.code) + " " + str(
                             posted_document.partner_id.parent_id.city_id.zipcode) + " " + str(posted_document.partner_id.parent_id.country_id.name)
                         },
                        {"Name": "DeliveryPoint",
                         "Value": str(posted_document.partner_id.street_12)
                         },
                        {"Name": "UbicationDelivery",
                         "Value": str(posted_document.partner_id.city_id.name) + " " + str(
                             posted_document.partner_id.state_id.code) + " " + str(
                             posted_document.partner_id.zip) + " " + str(posted_document.partner_id.country_id.name)
                         },
                        {"Name": "FLETE / FREIGHT",
                         "Value": round(
                             (posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop / posted_document.trm),
                             2) if posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop > 0 else 0},
                        {"Name": "SEGURO / INSURANCE",
                         "Value": posted_document.x_studio_field_3lEMz.x_studio_monto_seguro_usd_1},
                        {"Name": "OTROS / OTHERS",
                         "Value": round((posted_document.x_studio_field_3lEMz.x_studio_otros_cop / posted_document.trm),
                                        2) if posted_document.x_studio_field_3lEMz.x_studio_otros_cop > 0 else 0},
                        {"Name": "VALOR INCOTERM / TOTAL INCOTERM",
                         "Value": posted_document.amount_untaxed + tax_inclusive_amount},
                        {"Name": "INBOLSAS / INBAG",
#                         "Value": posted_document.payment_method.name},
                         "Value": 0},
                        {"Name": "VALOR LETRAS:",
                         "Value": numbertotext
                        }
                    ],
                    "PaymentSummary": {
                        "PaymentType": int(posted_document.partner_id.payment_type),
                        "PaymentMeans": int(posted_document.payment_method.key_dian),
                        "PaymentNote": posted_document.invoice_payment_term_id.name
                    },
                    "ItemInformation": self.load_invoice_line_data_to_json(template_id, posted_document),
                    "InvoiceTaxTotal": tax_total,
                    "InvoiceAllowanceCharge": [
                        {
                            "Id": "01",
                            "ChargeIndicator": "true",
                            "AllowanceChargeReason": "Flete",
                            "MultiplierFactorNumeric": 0,
                            "Amount": round(
                             (posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop / posted_document.trm),
                             2) if posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop > 0 else 0,
                            "BaseAmount": round(
                             (posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop / posted_document.trm),
                             2) if posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop > 0 else 0
                        },
                        {
                            "Id": "02",
                            "ChargeIndicator": "true",
                            "AllowanceChargeReason": "Seguro",
                            "MultiplierFactorNumeric": 0,
                            "Amount": posted_document.x_studio_field_3lEMz.x_studio_monto_seguro_usd_1,
                            "BaseAmount": posted_document.x_studio_field_3lEMz.x_studio_monto_seguro_usd_1
                        },
                        {
                            "Id": "03",
                            "ChargeIndicator": "true",
                            "AllowanceChargeReason": "Otros",
                            "MultiplierFactorNumeric": 0,
                            "Amount": round((posted_document.x_studio_field_3lEMz.x_studio_otros_cop / posted_document.trm),
                                        2) if posted_document.x_studio_field_3lEMz.x_studio_otros_cop > 0 else 0,
                            "BaseAmount": round((posted_document.x_studio_field_3lEMz.x_studio_otros_cop / posted_document.trm),
                                        2) if posted_document.x_studio_field_3lEMz.x_studio_otros_cop > 0 else 0
                        }
                    ],
                    "InvoiceTotal": {
#                        "LineExtensionAmount": posted_document.amount_untaxed,
#                        "LineExtensionAmount": posted_document.amount_untaxed - round(
                        "LineExtensionAmount": line_sub_total_tax,
                        "TaxExclusiveAmount": tax_exclusive_amount,
                        "TaxInclusiveAmount": line_sub_total_tax + tax_inclusive_amount,
                        "AllowanceTotalAmount": 0.0,

                        "PrePaidAmount": 0,  # posted_document.invoice_payments_widget,
                        "ChargeTotalAmount": line_tot_cargos,
                        "PayableAmount": posted_document.amount_untaxed + tax_inclusive_amount
                        # Deseable calcular los 4 campos
                    },
                "Documents": documents


             }


        if template_id == 91:
            tax_total = self.load_invoice_total_tax_to_json(template_id, posted_document)
            tax_exclusive_amount = 0
            tax_inclusive_amount = 0
            for tax in tax_total:
                if tax['TaxEvidenceIndicator'] == 'false':
                    tax_exclusive_amount += tax['TaxableAmount']
                    tax_inclusive_amount += tax['TaxAmount']
            data_json = {
                "CustomerInformation": {
                    "IdentificationType": posted_document.partner_id.document_type.key_dian,
                    "Identification": int(posted_document.partner_id.vat),
                    "DV": int(posted_document.partner_id.verification_code),
                    "RegistrationName": posted_document.partner_id.display_name,
                    "CountryCode": posted_document.partner_id.country_id.code,
                    "CountryName": posted_document.partner_id.country_id.name,
                    "SubdivisionCode": int(posted_document.partner_id.state_id.key_dian),
                    "SubdivisionName": posted_document.partner_id.state_id.name,
                    "CityCode": posted_document.partner_id.city_id.key_dian if posted_document.partner_id.country_id.code == "CO" else "",
                    "CityName": posted_document.partner_id.city_id.name,
                    "AddressLine": posted_document.partner_id.street,
                    "Telephone": posted_document.partner_id.phone,
                    "Email": posted_document.partner_id.email,
                    "CustomerCode": posted_document.partner_id.id,
                    "AdditionalAccountID": int(posted_document.partner_id.person_type.key_dian),
                    "TaxLevelCodeListName": int(
                        posted_document.partner_id.property_account_position_id.key_dian.key_dian),
                    "PostalZone": int(posted_document.partner_id.zip),
                    "TaxSchemeCode": "01" if posted_document.partner_id.property_account_position_id.key_dian.key_dian == '48' else 'ZY',
                    "TaxSchemeName": "IVA" if posted_document.partner_id.property_account_position_id.key_dian == '48' else 'No causa',
                    "FiscalResponsabilities": self.fiscal_responsabilities(posted_document),
                    "PartecipationPercent": 100,
                    "AdditionalCustomer": [{
                                            }],
                },
                "InvoiceGeneralInformation": {
                    "InvoiceAuthorizationNumber": posted_document.journal_id.invoice_resolution.resolution,
                    "PreinvoiceNumber": posted_document.number,
                    "InvoiceNumber": posted_document.number,

                    "IssueDate": str(posted_document.invoice_date),
                    "DaysOff": posted_document.invoice_payment_term_id.line_ids.days,
                    "Currency": posted_document.currency_id.name,
                    "ExchangeRate": float(posted_document.exchange_rate),
                    "ExchangeRateDate": str(posted_document.invoice_date),
                    "CustomizationID": "",
                    "SchemeID": "",
                    "SalesPerson": posted_document.invoice_user_id.name,
                    "Note": 'INGREDIENTS:' + str(posted_document.partner_id.x_studio_ingredientes) + ' PRODUCT OF COLOMBIA ' + 'FDA REGISTRATION NUMBER: 12218565886 ' + 'NET WEIGHT: ' + 'Kg / GROSS WEIGHT: ' + 'Kg  / TOTAL UNID: ' + '/ TOTAL CASES: ' + 'CONTAINER NUMBER: ' + str(posted_document.x_studio_field_3lEMz.x_studio_contenedor_asignado) + '/ ' + str(posted_document.x_studio_field_3lEMz.x_studio_descripcion_contenedor_1) + '/ NON PALETIZED CARGO /' + 'Goods to be resold under ' + 'TRADE NAME / KBCS-Pacifico Snacks-RSPO-0009.',
                    "ExternalGR": 'false',
                    "InvoiceDueDate": (posted_document.date + timedelta(
                        days=posted_document.invoice_payment_term_id.line_ids.days)).strftime("%Y-%m-%d"),
                    "StartDateTime": "0001-01-01T00:00:00",
                    "EndDateTime": "0001-01-01T00:00:00"
                },
                "Delivery": {
                    "AddressLine": str(posted_document.partner_id.street),
                    "CityCode": "",
                    "CityName": str(posted_document.partner_id.city_id.name),
                    "ContactPerson": "",
                    "CountryCode": "",
                    "CountryName": str(posted_document.partner_id.country_id.name),
                    "DeliveryDate": str(posted_document.invoice_date),
                    "DeliveryCompany": "",
                    "LossRiskResponsibilityCode": str(posted_document.x_studio_field_3lEMz.x_studio_incoterm_1 ) + str(posted_document.x_studio_field_3lEMz.x_studio_puerto_de_origen),
                    "SubdivisionCode": "",
                    "SubdivisionName": ""
                },
                "AdditionalDocuments": {
                    "OrderReference": "",
                    "OrderReferenceIssueDate": "0001-01-01T00:00:00",
                    "DespatchDocumentReference": 'DOC. INTERNO:' + str(posted_document.invoice_origin),
                    "DespatchDocumentIssueDate": "0001-01-01T00:00:00",
                    "ReceiptDocumentReference": "",
                    "ReceiptDocumentIssueDate": "0001-01-01T00:00:00",
                    "AdditionalDocument": []
                },
                "AdditionalDocumentReceipt": [],
                "AdditionalProperty": [
                    {"Name": "TEL/PHO:",
                     "Value": posted_document.partner_id.phone},
                    {"Name": "FLETE / FREIGHT",
                    "Value": round((posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop / posted_document.trm), 2) if posted_document.x_studio_field_3lEMz.x_studio_flete_origen_cop > 0 else 0},
                    {"Name": "SEGURO / INSURANCE",
                    "Value": posted_document.x_studio_field_3lEMz.x_studio_monto_seguro_usd_1},
                    {"Name": "OTROS / OTHERS",
                    "Value": round((posted_document.x_studio_field_3lEMz.x_studio_otros_cop / posted_document.trm), 2) if posted_document.x_studio_field_3lEMz.x_studio_otros_cop > 0 else 0},
                    {"Name": "VALOR INCOTERM / TOTAL INCOTERM",
                    "Value": posted_document.amount_untaxed + tax_inclusive_amount},
                    {"Name": "INBOLSAS / INBAG",
                    "Value": posted_document.payment_method.name}
                    ],
                "PaymentSummary": {
                   "PaymentType": "Debito" if posted_document.payment_type_1 == 1 else "Credito",
                   "PaymentMeans": int(posted_document.payment_method.key_dian),
                   "PaymentNote": "posted_document.invoice_payment_term.name"
                },

#                "NoteGeneralInformation": {
#                    "NoteNumber": posted_document.number,
#                    "CUFE": posted_document.reversed_entry_id.send_registry.cufe,
#                    "ReferenceID": posted_document.reversed_entry_id.name,
#                    "IssueDate": posted_document.reversed_entry_id.send_registry.status_date,
#                    "CustomizationID": 20,  # 1.1.18 Documento CreditNote
#                    "DiscrepancyCode": posted_document.reverse_concept.key_dian,
#                    "Currency": posted_document.currency_id.name,
#                    "Note": "",
#                    "ExternalGR": gr,
#                },
                "ItemInformation": self.load_invoice_line_data_to_json(template_id, posted_document),
                "NoteTaxTotal": tax_total,
                "NoteTotal": {
                    "LineExtensionAmount": posted_document.amount_untaxed,
                    "TaxExclusiveAmount": tax_exclusive_amount,
                    "TaxInclusiveAmount": posted_document.amount_untaxed + tax_inclusive_amount,
                    "AllowanceTotalAmount": 0.0,
                    "ChargeTotalAmount": 0.0,
                    "PrePaidAmount": 0,  # posted_document.invoice_payments_widget,
                    "PayableAmount": posted_document.amount_untaxed + tax_inclusive_amount
                },
                "NoteAllowanceCharge": []
            }

        return data_json

    def fiscal_responsabilities(self, posted_document):
        responsibility_con = " "
        for responsibility in posted_document.partner_id.fiscal_responsibility:
            if "R-99-PN" == responsibility.key_dian:
                return responsibility.key_dian
            else:
                responsibility_con = responsibility_con + str(
                    ";" if responsibility_con != " " else " ") + responsibility.key_dian
            return responsibility_con.strip()

    def insert_invoice(self, url, token, posted_document, gr, documents):
        """
        Función que envia la factura al servicio de Mis Facturas
        @author Luis Fernando calle - ETET
        @param gr: Representación grafica
        @param url: Base de la url (cambia si es produccion o si es pruebas) donde debe enviar la paeticion de insertar factura
        @param token: Token de acceso
        @param posted_document: Factura
        @param documents: Documentos para el body json
        """
        schema_id = posted_document.company_id.partner_id.document_type.key_dian
        id_number = posted_document.company_id.partner_id.vat

        if posted_document.journal_id.type == 'sale':
            if posted_document.partner_id.category_id:
                get_category = False
                for category in posted_document.partner_id.category_id:
                    if category.id == 100:
                        template_id = 217
                        get_category = True
                        break
                    elif category.id == 4:
                        template_id = 73
                        get_category = True
                        break
                if not get_category:
                    raise Warning(
                        'El cliente debe pertener a la categoría Cliente/Nacional o a la categoría Cliente/Exportación')
            else:
                raise Warning('El cliente no tiene asignado una categoría (Cliente/Nacional o Cliente/Exportación)')
        else:
            raise Warning('El Diario no corresponde a Tipo Venta)')

        url_service = url + "InsertInvoice?SchemaID=" + str(schema_id) + "&IDnumber=" + str(
            id_number) + "&TemplateID=" + str(template_id)
        payload = self.load_ed_data_to_json(template_id, posted_document, gr, documents)
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }
        print("\n", schema_id, "\n", id_number, "\n", template_id, "\n", url_service, "\n", payload, "\n", headers)
        response = requests.request("POST", url_service, headers=headers, json=payload)
        print(response.text.encode('utf8'))
        print(response.status_code)
        _logger.error(response.text.encode('utf8'))
        _logger.error(response.status_code)
        _logger.error(token)
        _logger.error(url_service)
        _logger.error(payload)

        if response.status_code == 200:
            time.sleep(2)
            electronic_document = self.get_electronic_document(url, token, posted_document,
                                                               response.json()['DocumentId'], document_type=1)
            json_electronic = electronic_document.json()
            print(json_electronic)
            detail_invoice = {
                'cufe': json_electronic['CUFE'],
                'document_key': response.json()['DocumentId'],
                'status_date': json_electronic['StatusDate'],
            }
            detail_send = {
                'date': datetime.now().date(),
                'code_response': electronic_document.status_code,
                'message_response': res[electronic_document.status_code],
                'type_action': 'validation',
                'type_document': 'json',
                'document_filename': 'status_invoice_' + str(posted_document.id) + '_' + str(
                    posted_document.number) + '.json',
                'document': base64.b64encode(
                    bytes(str(json.dumps(json_electronic, sort_keys=True, indent=4)), 'utf-8')),
                'is_attachment': True,
            }
#            send_registry = posted_document.cu_electronic_document_dian(posted_document.id, detail_invoice, 3)
            posted_document.cu_electronic_document_detail_dian(posted_document.id, detail_send, 1)
            posted_document.validate_status = True
            posted_document.send_status = True
            posted_document.message_status = response.text.encode('utf8')
            _logger.error('Factura Insertada')
        else:
            detail_send = {
                'date': datetime.now().date(),
                'code_response': response.status_code,
                'message_response': res[response.status_code],
                'type_action': 'send',
                'type_document': 'json',
                'document_filename': 'insert_invoice_' + str(posted_document.id) + '_' + str(
                    posted_document.number) + '.json',
                'document': base64.b64encode(bytes(str(json.dumps(payload, sort_keys=True, indent=4)), 'utf-8')),
                'is_attachment': True,
            }
            posted_document.cu_electronic_document_detail_dian(posted_document.id, detail_send, 2)
            posted_document.send_status = False
            posted_document.message_status = response.text.encode('utf8')
            _logger.error('Factura NO Insertada')

    def insert_note(self, url, token, posted_document, gr):
        schema_id = posted_document.company_id.partner_id.document_type.key_dian
        id_number = posted_document.company_id.partner_id.vat
        note_type = 91
        url_service = url + "insertnote?SchemaID=" + str(schema_id) + "&IDnumber=" + str(
            id_number) + "&NoteType=" + str(note_type)
        payload = self.load_ed_data_to_json(note_type, posted_document, gr, [])
        json_doc = json.dumps(payload, indent=4)
        print(str(json_doc))

        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }
        print("\n", schema_id, "\n", id_number, "\n", note_type, "\n", url_service, "\n", payload, "\n", headers)
        response = requests.request("POST", url_service, headers=headers, json=payload)
        print(response.text.encode('utf8'))
        print(response.status_code)

        detail_send = {
            'date': datetime.now().date(),
            'code_response': response.status_code,
            'message_response': res[response.status_code],
            'type_action': 'send',
            'type_document': 'json',
            'document_filename': 'insert_invoice_' + str(posted_document.id) + '_' + str(
                posted_document.number) + '.json',
            'document': base64.b64encode(bytes(str(json.dumps(payload, sort_keys=True, indent=4)), 'utf-8')),
            'is_attachment': True,
        }
        posted_document.cu_electronic_document_detail_dian(posted_document.id, detail_send, 2)

        if response.status_code == 200:
            time.sleep(2)
            electronic_document = self.get_electronic_document(url, token, posted_document,
                                                               response.json()['DocumentId'], document_type=2)
            json_electronic = electronic_document.json()
            print(json_electronic)
            detail_invoice = {
                'cufe': json_electronic['CUFE'],
                'document_key': response.json()['DocumentId'],
                'status_date': json_electronic['StatusDate'],
            }
            detail_send = {
                'date': datetime.now().date(),
                'code_response': electronic_document.status_code,
                'message_response': res[electronic_document.status_code],
                'type_action': 'validation',
                'type_document': 'json',
                'document_filename': 'status_invoice_' + str(posted_document.id) + '_' + str(
                    posted_document.number) + '.json',
                'document': base64.b64encode(
                    bytes(str(json.dumps(json_electronic, sort_keys=True, indent=4)), 'utf-8')),
                'is_attachment': False,
            }

            send_registry = posted_document.cu_electronic_document_dian(posted_document.id, detail_invoice, 3)
            posted_document.cu_electronic_document_detail_dian(posted_document.id, detail_send, 2)
        else:
            raise exceptions.ValidationError(response.text.split('"')[3])

    def get_electronic_document(self, url, token, posted_document, document_id, document_type):
        schema_id = posted_document.company_id.partner_id.document_type.key_dian
        id_number = posted_document.company_id.partner_id.vat
        url_service = url + "GetDocumentStatus?SchemaID=" + str(schema_id) + "&IDNumber=" + str(
            id_number) + "&DocumentId=" + str(document_id) + "&DocumentType=" + str(document_type)
        payload = {}
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url_service, headers=headers, data=payload)
        return response

    def attach_rg(self, url, token, posted_document, b64):
        schema_id = posted_document.company_id.partner_id.document_type.key_dian
        id_number = posted_document.company_id.partner_id.vat
        document_id = posted_document.send_registry.document_key
        document_type = 1 if posted_document.type == "out_invoice" else 2
        print("document_type: ", document_type)
        url_service = url + "AttachRG?SchemaID=" + str(schema_id) + "&IDNumber=" + str(
            id_number) + "&DocumentId=" + str(document_id) + "&DocumentType=" + str(document_type)
        payload = {}
        files = [
            ('File', base64.decodebytes(b64))
        ]
        headers = {
            'Authorization': token,
        }
        response = requests.request("POST", url_service, headers=headers, data=payload, files=files)
        print("--RG--")
        print(response.text.encode('utf8'))
        print(response.status_code)
        detail_send = {
            'date': datetime.now().date(),
            'code_response': response.status_code,
            'message_response': res[response.status_code],
            'type_action': 'gr',
            'type_document': 'pdf',
            'document_filename': '',
            'document': '',
            'is_attachment': False,
        }
        posted_document.cu_electronic_document_detail_dian(posted_document.id, detail_send, 4)

    def insert_attachment(self, url, token, posted_document, file):
        schema_id = posted_document.company_id.partner_id.document_type.key_dian
        id_number = posted_document.company_id.partner_id.vat
        url_service = url + "InsertAttachment?SchemaID=" + str(schema_id) + "&IDNumber=" + str(id_number)
        payload = {}
        print("----- ", str(file))
        files = file
        headers = {
            'Authorization': token,
        }
        response = requests.request("POST", url_service, headers=headers, data=payload, files=files)
        print(response.text.encode('utf8'))
        detail_send = {
            'date': datetime.now().date(),
            'code_response': response.status_code,
            'message_response': res[response.status_code],
            'type_action': 'attachment',
            'type_document': None,
            'document_filename': None,
            'document': None,
            'is_attachment': False,
        }
        return_data = [response.json(), detail_send]
        return return_data

    def send_electronic_document(self, posted_document):
        parameter = self._get_parameters_connection()
        parameter_settings = self._get_parameters_settings()
        send = None
        if posted_document.type == 'out_invoice':
#           list_document_invoice = self.get_document_attachment(parameter['url'], parameter['token'], posted_document)
            list_document_invoice = False
            send = None
            send = self.insert_invoice(parameter['url'], parameter['token'], posted_document, parameter_settings['fe_own_gr'], list_document_invoice)

        if posted_document.type == 'out_refund':
            send = None
            #send = self.insert_note(parameter['url'], parameter['token'], posted_document,parameter_settings['fe_own_gr'])

        return send

    def send_rg_electronic_document(self, b64, posted_document):
        parameter = self._get_parameters_connection()
        self.attach_rg(parameter['url'], parameter['token'], posted_document, b64)

    def get_document_attachment(self, url, token, posted_document):
        attachments = self.env['ir.attachment'].search(
            [('res_model', '=', 'account.move'), ('res_id', '=', posted_document.id)])
        list_document_invoice = []
        for attach in attachments:
            list_tup_file = [(attach.name, base64.decodebytes(attach.datas))]
            file_attach = self.insert_attachment(url, token, posted_document, list_tup_file)
            print(str(file_attach))
            dic_file = {'Name': file_attach[0]['FileMailBoxList'][0]['FileName'],
                        'ID': file_attach[0]['FileMailBoxList'][0]['FileMailBoxUUID']}
            attach.update({
                'fe_filename': file_attach[0]['FileMailBoxList'][0]['FileName'],
                'fe_file_code': file_attach[0]['FileMailBoxList'][0]['FileMailBoxUUID']
            })
            file_attach[1]['type_document']: attach.mimetype.split("/")[1]
            file_attach[1]['document_filename']: attach.name
            file_attach[1]['document']: attach.datas
            list_document_invoice.append(dic_file)
            print(file_attach[1])
            posted_document.cu_electronic_document_detail_dian(posted_document.id, file_attach[1], 1)

        return list_document_invoice
