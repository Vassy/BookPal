odoo.define('show_chatter_on_modal.form_renderer.js', function (require) {
"use strict";

    const FormRenderer = require('web.FormRenderer');
    require('@mail/widgets/form_renderer/form_renderer');

    FormRenderer.include({
        _renderNode: function (node){
            if (node.tag === 'div' && node.attrs.class === 'oe_chatter') {
                return this._makeChatterContainerTarget();
            }else{
                return this._super.apply(this, arguments);
            }            
        },
    });

});
