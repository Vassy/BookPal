
odoo.define('bista_inno_extend.basic_fields_extends', function (require) {
    // The goal of this file is to contain JS hacks related to allowing
    // section and note on sale order and invoice.
    
    // [UPDATED] now also allows configuring products on sale order.
    
    "use strict";
    var JournalDashboardGraph = require('web.basic_fields').JournalDashboardGraph;
    JournalDashboardGraph.include({
        _renderInDOM: function () {
            if(this.$el == undefined){
                return
            }
            this.$el.empty();
            var config, cssClass;
            if (this.graph_type === 'line') {
                config = this._getLineChartConfig();
                cssClass = 'o_graph_linechart';
            } else if (this.graph_type === 'bar') {
                config = this._getBarChartConfig();
                cssClass = 'o_graph_barchart';
            }
            this.$canvas = $('<canvas/>');
            this.$el.addClass(cssClass);
            this.$el.empty();
            this.$el.append(this.$canvas);
            var context = this.$canvas[0].getContext('2d');
            this.chart = new Chart(context, config);
        },
    });
})