odoo.define("bista_sales_approval.QtyAtDateWidget", function(require) {
    "use strict";

    var utils = require("web.utils");
    var QtyAtDateWidget = require("sale_stock.QtyAtDateWidget");

    QtyAtDateWidget.include({
        _updateData: function() {
            // add some data to simplify the template
            if (this.data.scheduled_date) {
                var qty_to_deliver = utils.round_decimals(this.data.qty_to_deliver, this.fields.qty_to_deliver.digits[1]);
                if (this.data.state === "sale") {
                    this.data.will_be_fulfilled = utils.round_decimals(this.data.free_qty_today, this.fields.free_qty_today.digits[1]) >= qty_to_deliver
                } else {
                    this.data.will_be_fulfilled = utils.round_decimals(this.data.virtual_available_at_date, this.fields.virtual_available_at_date.digits[1]) >= qty_to_deliver
                }
                this.data.will_be_late = this.data.forecast_expected_date && this.data.forecast_expected_date > this.data.scheduled_date;
                if (!["sale", "done", "cancel"].includes(this.data.state)) {
                    // Moves aren't created yet, then the forecasted is only based on virtual_available of quant
                    this.data.forecasted_issue = !this.data.will_be_fulfilled && !this.data.is_mto;
                } else {
                    // Moves are created, using the forecasted data of related moves
                    this.data.forecasted_issue = !this.data.will_be_fulfilled || this.data.will_be_late;
                }
            }
        },
    });
});
