# -*- encoding: utf-8 -*-

from odoo import models, fields, _

from odoo.addons.delivery_ups.models.ups_request import Package
from .ups_request import UPSRequest


class ProviderUPS(models.Model):
    _inherit = "delivery.carrier"

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
