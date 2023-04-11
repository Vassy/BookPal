# -*- encoding: utf-8 -*-

from odoo import models, fields, _

from odoo.addons.delivery_ups.models.ups_request import Package
from .ups_request import UPSRequest
from odoo.tools import pdf
from odoo.exceptions import UserError


class ProviderUPS(models.Model):
    _inherit = "delivery.carrier"

    # Inherited to stop adding labels in all pickings
    def ups_send_shipping(self, pickings):
        res = []
        superself = self.sudo()
        srm = UPSRequest(self.log_xml, superself.ups_username, superself.ups_passwd, superself.ups_shipper_number, superself.ups_access_number, self.prod_environment)
        ResCurrency = self.env['res.currency']
        for picking in pickings:
            packages = []
            package_names = []
            if picking.package_ids:
                # Create all packages
                for package in picking.package_ids:
                    packages.append(Package(self, package.shipping_weight, quant_pack=package.package_type_id, name=package.name))
                    package_names.append(package.name)
            # Create one package with the rest (the content that is not in a package)
            if picking.weight_bulk:
                packages.append(Package(self, picking.weight_bulk))

            shipment_info = {
                'description': picking.origin,
                'total_qty': sum(sml.qty_done for sml in picking.move_line_ids),
                'ilt_monetary_value': '%d' % sum(sml.sale_price for sml in picking.move_line_ids),
                'itl_currency_code': self.env.company.currency_id.name,
                'phone': picking.partner_id.mobile or picking.partner_id.phone or picking.sale_id.partner_id.mobile or picking.sale_id.partner_id.phone,
            }
            if picking.sale_id and picking.sale_id.carrier_id != picking.carrier_id:
                ups_service_type = picking.carrier_id.ups_default_service_type or self.ups_default_service_type
            else:
                ups_service_type = self.ups_default_service_type
            ups_carrier_account = False
            if self.ups_bill_my_account:
                ups_carrier_account = picking.partner_id.with_company(picking.company_id).property_ups_carrier_account

            if picking.carrier_id.ups_cod:
                cod_info = {
                    'currency': picking.partner_id.country_id.currency_id.name,
                    'monetary_value': picking.sale_id.amount_total,
                    'funds_code': self.ups_cod_funds_code,
                }
            else:
                cod_info = None

            check_value = srm.check_required_value(picking.company_id.partner_id, picking.picking_type_id.warehouse_id.partner_id, picking.partner_id, picking=picking)
            if check_value:
                raise UserError(check_value)

            package_type = picking.package_ids and picking.package_ids[0].package_type_id.shipper_package_code or self.ups_default_package_type_id.shipper_package_code
            srm.send_shipping(
                shipment_info=shipment_info, packages=packages, shipper=picking.company_id.partner_id, ship_from=picking.picking_type_id.warehouse_id.partner_id,
                ship_to=picking.partner_id, packaging_type=package_type, service_type=ups_service_type, duty_payment=picking.carrier_id.ups_duty_payment,
                label_file_type=self.ups_label_file_type, ups_carrier_account=ups_carrier_account, saturday_delivery=picking.carrier_id.ups_saturday_delivery,
                cod_info=cod_info)
            result = srm.process_shipment()
            if result.get('error_message'):
                raise UserError(result['error_message'].__str__())

            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.company
            currency_order = picking.sale_id.currency_id
            if not currency_order:
                currency_order = picking.company_id.currency_id

            if currency_order.name == result['currency_code']:
                price = float(result['price'])
            else:
                quote_currency = ResCurrency.search([('name', '=', result['currency_code'])], limit=1)
                price = quote_currency._convert(
                    float(result['price']), currency_order, company, order.date_order or fields.Date.today())

            package_labels = []
            for track_number, label_binary_data in result.get('label_binary_data').items():
                package_labels = package_labels + [(track_number, label_binary_data)]
            carrier_tracking_ref = "+".join([pl[0] for pl in package_labels])
            logmessage = _("Shipment created into UPS<br/>"
                           "<b>Tracking Numbers:</b> %s<br/>"
                           "<b>Packages:</b> %s") % (carrier_tracking_ref, ','.join(package_names))
            if self.ups_label_file_type != 'GIF':
                attachments = [('LabelUPS-%s.%s' % (pl[0], self.ups_label_file_type), pl[1]) for pl in package_labels]
            if self.ups_label_file_type == 'GIF':
                attachments = [('LabelUPS.pdf', pdf.merge_pdf([pl[1] for pl in package_labels]))]
            picking.message_post(body=logmessage, attachments=attachments)
            shipping_data = {
                'exact_price': price,
                'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
            if self.return_label_on_delivery:
                self.ups_get_return_label(picking)
        return res

    def ups_rate_shipment(self, order):
        superself = self.sudo()
        srm = UPSRequest(
            self.log_xml,
            superself.ups_username,
            superself.ups_passwd,
            superself.ups_shipper_number,
            superself.ups_access_number,
            self.prod_environment,
        )
        ResCurrency = self.env["res.currency"]
        max_weight = self.ups_default_package_type_id.max_weight
        dropship_id = self.env.ref("stock_dropshipping.route_drop_shipping")
        dropship_line = order.order_line.filtered(lambda l: l.route_id == dropship_id)
        non_dropship_line = order.order_line.filtered(
            lambda l: l.route_id != dropship_id and not l.is_delivery and not l.display_type
        )
        total_price = 0
        if non_dropship_line:
            packages = []
            total_qty = 0
            total_weight = 0
            for line in non_dropship_line.filtered(
                lambda l: l.product_id.type in ["product", "consu"]
                and not l.is_delivery
                and not l.display_type
            ):
                total_weight += line.product_qty * line.product_id.weight
            for line in non_dropship_line:
                total_qty += line.product_uom_qty

            if max_weight and total_weight > max_weight:
                total_package = int(total_weight / max_weight)
                last_package_weight = total_weight % max_weight

                for seq in range(total_package):
                    packages.append(Package(self, max_weight))
                if last_package_weight:
                    packages.append(Package(self, last_package_weight))
            else:
                packages.append(Package(self, total_weight))

            # required when service type = 'UPS Worldwide Express Freight'
            shipment_info = {"total_qty": total_qty}

            if self.ups_cod:
                cod_info = {
                    "currency": order.partner_id.country_id.currency_id.name,
                    "monetary_value": order.amount_total,
                    "funds_code": self.ups_cod_funds_code,
                }
            else:
                cod_info = None

            check_value = srm.check_required_value(
                order.company_id.partner_id,
                order.warehouse_id.partner_id,
                order.partner_shipping_id,
                order=order,
            )
            if check_value:
                return {
                    "success": False,
                    "price": 0.0,
                    "error_message": check_value,
                    "warning_message": False,
                }

            ups_service_type = self.ups_default_service_type
            result = srm.get_shipping_price(
                shipment_info=shipment_info,
                packages=packages,
                shipper=order.company_id.partner_id,
                ship_from=order.warehouse_id.partner_id,
                ship_to=order.partner_shipping_id,
                packaging_type=self.ups_default_package_type_id.shipper_package_code,
                service_type=ups_service_type,
                saturday_delivery=self.ups_saturday_delivery,
                cod_info=cod_info,
            )

            if result.get("error_message"):
                return {
                    "success": False,
                    "price": 0.0,
                    "error_message": _("Error:\n%s", result["error_message"]),
                    "warning_message": False,
                }

            if order.currency_id.name == result["currency_code"]:
                price = float(result["price"])
            else:
                quote_currency = ResCurrency.search(
                    [("name", "=", result["currency_code"])], limit=1
                )
                price = quote_currency._convert(
                    float(result["price"]),
                    order.currency_id,
                    order.company_id,
                    order.date_order or fields.Date.today(),
                )

            if self.ups_bill_my_account and order.partner_ups_carrier_account:
                # Don't show delivery amount, if ups bill my account option is true
                price = 0.0
            total_price = price

        for line in dropship_line:
            packages = []
            total_qty = line.product_uom_qty
            total_weight = line.product_qty * line.product_id.weight

            if max_weight and total_weight > max_weight:
                total_package = int(total_weight / max_weight)
                last_package_weight = total_weight % max_weight

                for seq in range(total_package):
                    packages.append(Package(self, max_weight))
                if last_package_weight:
                    packages.append(Package(self, last_package_weight))
            else:
                packages.append(Package(self, total_weight))

            shipment_info = {"total_qty": total_qty}

            if self.ups_cod:
                cod_info = {
                    "currency": order.partner_id.country_id.currency_id.name,
                    "monetary_value": order.amount_total,
                    "funds_code": self.ups_cod_funds_code,
                }
            else:
                cod_info = None

            check_value = srm.check_required_value_vendor(
                order.company_id.partner_id,
                line.supplier_id,
                order.partner_shipping_id,
                order=order,
            )
            if check_value:
                return {
                    "success": False,
                    "price": 0.0,
                    "error_message": check_value,
                    "warning_message": False,
                }

            ups_service_type = self.ups_default_service_type
            result = srm.get_shipping_price(
                shipment_info=shipment_info,
                packages=packages,
                shipper=order.company_id.partner_id,
                ship_from=line.supplier_id,
                ship_to=order.partner_shipping_id,
                packaging_type=self.ups_default_package_type_id.shipper_package_code,
                service_type=ups_service_type,
                saturday_delivery=self.ups_saturday_delivery,
                cod_info=cod_info,
            )

            if result.get("error_message"):
                return {
                    "success": False,
                    "price": 0.0,
                    "error_message": _("Error:\n%s", result["error_message"]),
                    "warning_message": False,
                }

            if order.currency_id.name == result["currency_code"]:
                price = float(result["price"])
            else:
                quote_currency = ResCurrency.search(
                    [("name", "=", result["currency_code"])], limit=1
                )
                price = quote_currency._convert(
                    float(result["price"]),
                    order.currency_id,
                    order.company_id,
                    order.date_order or fields.Date.today(),
                )

            if self.ups_bill_my_account and order.partner_ups_carrier_account:
                # Don't show delivery amount, if ups bill my account option is true
                price = 0.0

            line.write({"vendor_shipping_cost": price})
            total_price += price

        return {
            "success": True,
            "price": total_price,
            "error_message": False,
            "warning_message": False,
        }
