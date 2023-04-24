from odoo import fields, models


class AccountAvatax(models.AbstractModel):
    _inherit = "account.avatax"

    def _get_avatax_taxes(self, commit):
        # Overide method to calculate tax based on shipping partner.
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        if self._name in ("sale.order", "account.move") and self.partner_shipping_id:
            partner = self.partner_shipping_id
        if self._context.get("partner"):
            partner = self._context.get("partner")
        document_date, tax_date = self._get_avatax_dates()
        taxes = {
            "addresses": self._get_avatax_addresses(self._get_avatax_ship_to_partner()),
            "companyCode": self.company_id.partner_id.avalara_partner_code or "",
            "customerCode": partner.avalara_partner_code or partner.avatax_unique_code,
            "entityUseCode": partner.with_company(
                self.company_id
            ).avalara_exemption_id.code
            or "",
            "businessIdentificationNo": partner.vat or "",
            "date": (document_date or fields.Date.today()).isoformat(),
            "lines": self._get_avatax_invoice_lines(),
            "type": self._get_avatax_document_type(),
            "code": self.avatax_unique_code,
            "referenceCode": self._get_avatax_ref(),
            "currencyCode": self.currency_id.name or "",
            "commit": commit and self.company_id.avalara_commit,
        }
        if tax_date:
            taxes["taxOverride"] = {
                "type": "taxDate",
                "reason": "Manually changed the tax calculation date",
                "taxDate": tax_date.isoformat(),
            }
        return taxes
