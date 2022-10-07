odoo.define('website_bookpal_inquiry.website_bookpal_inquiry', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const {_t, qweb} = require('web.core');

    publicWidget.registry.inquiry_form = publicWidget.Widget.extend({
        selector: '#website-inquiry',
        xmlDependencies: ['/website_bookpal_inquiry/static/src/xml/website_bookpal_inquiry.xml'],
//        disabledInEditableMode: false,
        start: function () {
            return this._super.apply(this, arguments).then(() => {
                this.$el.on('keypress', function (event){
                    if (event.which === 13) {
                        event.preventDefault();
                    }
                });
                this.$elProduct = this.$el.find('.product_id')
                    .select2({
                         minimumInputLength: 2,
//                         query: (query) => {
//                             this._rpc({
//                                  model: 'product.product',
//                                  method: 'search_read',
//                                  domain: [['name','ilike', query]],
//                                  fields: ['id','display_name'],
//                             }).then((results) => {
//                                debugger
//                                 let options = {results: []};
//                                 results.unshift({
//                                     'id': '',
//                                     'name': '--- Select Product ---',
//                                     'display_name': '--- Select Product ---',
//                                 });
//                                 _.map(results, function (rec) {
//                                     options.results.push({
//                                         id: rec.id,
//                                         text: rec.display_name,
//                                         record: rec,
//                                     });
//                                 });
//                                 query.callback(options);
//                             });
//                         },
                        formatResult: function (data) {
                            let record = $(data.element[0]).data('record');
                            debugger
                            return qweb.render('website_bookpal_inquiry.product', {
                                product: record
                            });
                        },
                    })
//                    .on("change", this._onChangeProductVariant.bind(this));
//                    this.$elProduct.trigger('change');
            });
        },
    });
});
