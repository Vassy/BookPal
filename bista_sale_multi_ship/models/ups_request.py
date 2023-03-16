# -*- coding: utf-8 -*-

from odoo import _, _lt

from odoo.addons.delivery_ups.models.ups_request import UPSRequest as UPS
from odoo.addons.delivery_ups.models.ups_request import UPS_ERROR_MAP

UPS_ERROR_MAP.update(
    {"120313123": _lt("Vendor Phone must be at least 10 alphanumeric characters.")}
)

def send_shipping_ec(self, shipment_info, packages, shipper, ship_from, ship_to, packaging_type, service_type, saturday_delivery, duty_payment, cod_info=None, label_file_type='GIF', ups_carrier_account=False):
    client = self._set_client(self.ship_wsdl, 'Ship', 'ShipmentRequest')
    request = self.factory_ns3.RequestType()
    request.RequestOption = 'nonvalidate'

    request_type = "shipping"
    label = self.factory_ns2.LabelSpecificationType()
    label.LabelImageFormat = self.factory_ns2.LabelImageFormatType()
    label.LabelImageFormat.Code = label_file_type
    label.LabelImageFormat.Description = label_file_type
    if label_file_type != 'GIF':
        label.LabelStockSize = self.factory_ns2.LabelStockSizeType()
        label.LabelStockSize.Height = '6'
        label.LabelStockSize.Width = '4'

    shipment = self.factory_ns2.ShipmentType()
    shipment.Description = shipment_info.get('description')

    for package in self.set_package_detail(client, packages, packaging_type, ship_from, ship_to, cod_info, request_type):
        shipment.Package.append(package)

    shipment.Shipper = self.factory_ns2.ShipperType()
    shipment.Shipper.Address = self.factory_ns2.ShipAddressType()
    shipment.Shipper.AttentionName = (shipper.name or '')[:35]
    shipment.Shipper.Name = (shipper.parent_id.name or shipper.name or '')[:35]
    shipment.Shipper.Address.AddressLine = [l for l in [shipper.street or '', shipper.street2 or ''] if l]
    shipment.Shipper.Address.City = shipper.city or ''
    shipment.Shipper.Address.PostalCode = shipper.zip or ''
    shipment.Shipper.Address.CountryCode = shipper.country_id.code or ''
    if shipper.country_id.code in ('US', 'CA', 'IE'):
        shipment.Shipper.Address.StateProvinceCode = shipper.state_id.code or ''
    shipment.Shipper.ShipperNumber = self.shipper_number or ''
    shipment.Shipper.Phone = self.factory_ns2.ShipPhoneType()
    shipment.Shipper.Phone.Number = self._clean_phone_number(shipper.phone)

    shipment.ShipFrom = self.factory_ns2.ShipFromType()
    shipment.ShipFrom.Address = self.factory_ns2.ShipAddressType()
    shipment.ShipFrom.AttentionName = (ship_from.name or '')[:35]
    shipment.ShipFrom.Name = (ship_from.parent_id.name or ship_from.name or '')[:35]
    shipment.ShipFrom.Address.AddressLine = [l for l in [ship_from.street or '', ship_from.street2 or ''] if l]
    shipment.ShipFrom.Address.City = ship_from.city or ''
    shipment.ShipFrom.Address.PostalCode = ship_from.zip or ''
    shipment.ShipFrom.Address.CountryCode = ship_from.country_id.code or ''
    if ship_from.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipFrom.Address.StateProvinceCode = ship_from.state_id.code or ''
    shipment.ShipFrom.Phone = self.factory_ns2.ShipPhoneType()
    shipment.ShipFrom.Phone.Number = self._clean_phone_number(ship_from.phone)

    shipment.ShipTo = self.factory_ns2.ShipToType()
    shipment.ShipTo.Address = self.factory_ns2.ShipToAddressType()
    shipment.ShipTo.AttentionName = (ship_to.name or '')[:35]
    shipment.ShipTo.Name = (ship_to.external_company if ship_to.external_company else ship_to.parent_id.name or ship_to.name or '')[:35]
    shipment.ShipTo.Address.AddressLine = [l for l in [ship_to.street or '', ship_to.street2 or ''] if l]
    shipment.ShipTo.Address.City = ship_to.city or ''
    shipment.ShipTo.Address.PostalCode = ship_to.zip or ''
    shipment.ShipTo.Address.CountryCode = ship_to.country_id.code or ''
    if ship_to.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipTo.Address.StateProvinceCode = ship_to.state_id.code or ''
    shipment.ShipTo.Phone = self.factory_ns2.ShipPhoneType()
    shipment.ShipTo.Phone.Number = self._clean_phone_number(shipment_info['phone'])
    if not ship_to.commercial_partner_id.is_company:
        shipment.ShipTo.Address.ResidentialAddressIndicator = None

    shipment.Service = self.factory_ns2.ServiceType()
    shipment.Service.Code = service_type or ''
    shipment.Service.Description = 'Service Code'
    if service_type == "96":
        shipment.NumOfPiecesInShipment = int(shipment_info.get('total_qty'))
    shipment.ShipmentRatingOptions = self.factory_ns2.RateInfoType()
    shipment.ShipmentRatingOptions.NegotiatedRatesIndicator = 1
    # Shipments from US to CA or PR require extra info
    if ship_from.country_id.code == 'US' and ship_to.country_id.code in ['CA', 'PR']:
        shipment.InvoiceLineTotal = self.factory_ns2.CurrencyMonetaryType()
        shipment.InvoiceLineTotal.CurrencyCode = shipment_info.get('itl_currency_code')
        shipment.InvoiceLineTotal.MonetaryValue = shipment_info.get('ilt_monetary_value')

    # set the default method for payment using shipper account
    payment_info = self.factory_ns2.PaymentInfoType()
    shipcharge = self.factory_ns2.ShipmentChargeType()
    shipcharge.Type = '01'

    # Bill Recevier 'Bill My Account'
    if ups_carrier_account:
        shipcharge.BillReceiver = self.factory_ns2.BillReceiverType()
        shipcharge.BillReceiver.Address = self.factory_ns2.BillReceiverAddressType()
        shipcharge.BillReceiver.AccountNumber = ups_carrier_account
        shipcharge.BillReceiver.Address.PostalCode = ship_to.zip
    else:
        shipcharge.BillShipper = self.factory_ns2.BillShipperType()
        shipcharge.BillShipper.AccountNumber = self.shipper_number or ''

    payment_info.ShipmentCharge = [shipcharge]

    if duty_payment == 'SENDER':
        duty_charge = self.factory_ns2.ShipmentChargeType()
        duty_charge.Type = '02'
        duty_charge.BillShipper = self.factory_ns2.BillShipperType()
        duty_charge.BillShipper.AccountNumber = self.shipper_number or ''
        payment_info.ShipmentCharge.append(duty_charge)

    shipment.PaymentInformation = payment_info

    if saturday_delivery:
        shipment.ShipmentServiceOptions = self.factory_ns2.ShipmentServiceOptionsType()
        shipment.ShipmentServiceOptions.SaturdayDeliveryIndicator = saturday_delivery
    else:
        shipment.ShipmentServiceOptions = ''
    self.shipment = shipment
    self.label = label
    self.request = request
    self.label_file_type = label_file_type

UPS.send_shipping = send_shipping_ec

class UPSRequest(UPS):
    def check_required_value_vendor(
        self, shipper, ship_from, ship_to, order=False, picking=False
    ):
        required_field = {"city": "City", "country_id": "Country", "phone": "Phone"}
        # Check required field for shipper
        res = [required_field[field] for field in required_field if not shipper[field]]
        if shipper.country_id.code in ("US", "CA", "IE") and not shipper.state_id.code:
            res.append("State")
        if not shipper.street and not shipper.street2:
            res.append("Street")
        if shipper.country_id.code != "HK" and not shipper.zip:
            res.append("ZIP code")
        if res:
            return _(
                "The address of your company is missing or wrong."
                "\n(Missing field(s) : %s)",
                ",".join(res),
            )
        if len(self._clean_phone_number(shipper.phone)) < 10:
            return str(UPS_ERROR_MAP.get("120115"))
        # Check required field for warehouse address
        res = [
            required_field[field] for field in required_field if not ship_from[field]
        ]
        if (
            ship_from.country_id.code in ("US", "CA", "IE")
            and not ship_from.state_id.code
        ):
            res.append("State")
        if not ship_from.street and not ship_from.street2:
            res.append("Street")
        if ship_from.country_id.code != "HK" and not ship_from.zip:
            res.append("ZIP code")
        if res:
            return _(
                "The address of your Vendor is missing or wrong."
                "\n(Missing field(s) : %s)",
                ",".join(res),
            )
        if len(self._clean_phone_number(ship_from.phone)) < 10:
            return str(UPS_ERROR_MAP.get("120313123"))
        # Check required field for recipient address
        res = [
            required_field[field]
            for field in required_field
            if field != "phone" and not ship_to[field]
        ]
        if ship_to.country_id.code in ("US", "CA", "IE") and not ship_to.state_id.code:
            res.append("State")
        if not ship_to.street and not ship_to.street2:
            res.append("Street")
        if ship_to.country_id.code != "HK" and not ship_to.zip:
            res.append("ZIP code")
        if len(ship_to.street or "") > 35 or len(ship_to.street2 or "") > 35:
            return _(
                "UPS address lines can only contain a maximum of 35 characters. You can "
                "split the contacts addresses on multiple lines to try to avoid this "
                "limitation."
            )
        if picking and not order:
            order = picking.sale_id
        phone = ship_to.mobile or ship_to.phone
        if order and not phone:
            phone = order.partner_id.mobile or order.partner_id.phone
        if order:
            if not order.order_line:
                return _("Please provide at least one item to ship.")
            error_lines = order.order_line.filtered(
                lambda line: not line.product_id.weight
                and not line.is_delivery
                and line.product_id.type != "service"
                and not line.display_type
            )
            if error_lines:
                return _(
                    "The estimated shipping price cannot be computed because the weight "
                    "is missing for the following product(s): \n %s"
                ) % ", ".join(error_lines.product_id.mapped("name"))
        if picking:
            for ml in picking.move_line_ids.filtered(
                lambda ml: not ml.result_package_id and not ml.product_id.weight
            ):
                return _(
                    "The delivery cannot be done because the weight of your "
                    "product is missing."
                )
            packages_without_weight = picking.move_line_ids.mapped(
                "result_package_id"
            ).filtered(lambda p: not p.shipping_weight)
            if packages_without_weight:
                return _(
                    "Packages %s do not have a positive shipping weight.",
                    ", ".join(packages_without_weight.mapped("display_name")),
                )
        if not phone:
            res.append("Phone")
        if res:
            return _(
                "The recipient address is missing or wrong.\n(Missing field(s) : %s)",
                ",".join(res),
            )
        if len(self._clean_phone_number(phone)) < 10:
            return str(UPS_ERROR_MAP.get("120213"))
        return False
