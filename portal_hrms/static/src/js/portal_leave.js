odoo.define('portal_hrms.button', function(require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const { handleCheckIdentity } = require('portal.portal');

    publicWidget.registry.RemoveLeave = publicWidget.Widget.extend({
        selector: '#leave_row + * .fa.fa-trash.text-danger',
        events: {
            click: '_onClick'
        },

        async _onClick(e) {
        debugger;
            e.preventDefault();
            await handleCheckIdentity(
                this.proxy('_rpc'),
                this._rpc({
                    model: 'hr.leave',
                    method: 'unlink',
                    args: [parseInt(this.target.id)]
                })
            );
            window.location = window.location;
        }
    });
});