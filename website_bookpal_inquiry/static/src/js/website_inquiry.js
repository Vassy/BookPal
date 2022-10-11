odoo.define('website_bookpal_inquiry.website_bookpal_inquiry', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const {_t, qweb} = require('web.core');
    var ajax = require('web.ajax');

    publicWidget.registry.inquiry_form = publicWidget.Widget.extend({
        selector: '#website-inquiry',
        xmlDependencies: ['/website_bookpal_inquiry/static/src/xml/website_bookpal_inquiry.xml'],
        events: {
            'click .submit': '_onSubmitForm',
        },
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
                        formatResult: function (data) {
                            let record = $(data.element[0]).data('record');
                            return qweb.render('website_bookpal_inquiry.product', {
                                product: record
                            });
                        },
                    })
            });
        },
        _onSubmitForm: function(ev){
            ev.preventDefault();

            this.form_fields = this.$target.serializeArray();

            var email = this.$target.find('[name="email"]').val();
            var re = /\S+@\S+\.\S+/;
            if (!email || !re.test(email)){
                this.$target.find('[name="email"]').addClass('is-invalid');
                return true;
            } else {
                this.$target.find('[name="email"]').removeClass('is-invalid');
            }
            var form_values = {};
            _.each(this.form_fields, function (input) {
                if (input.name in form_values) {
                    if (Array.isArray(form_values[input.name])) {
                        form_values[input.name].push(input.value);
                    } else {
                        form_values[input.name] = [form_values[input.name], input.value];
                    }
                } else {
                    if (input.value !== '') {
                        form_values[input.name] = input.value;
                    }
                }
            });

            ajax.post(this.$target.attr('action') || '/inquiry', form_values)
            .then(function (result_data) {
                result_data = JSON.parse(result_data);
                if (result_data.sale_order_name){
                    var big_commerce_link = 'https://store-wiw3i6m4o6.mybigcommerce.com/'
                    if(confirm("You will get email shortly!")){
                        window.location.href = big_commerce_link
                    } else {
                        window.location.href = big_commerce_link
                    }
                }
            });
        }
    });
});
