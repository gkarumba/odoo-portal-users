odoo.define('portal_hrms.attendance', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.omniPortalAttendance = publicWidget.Widget.extend({
        selector: '.o_portal',
        events: {
            "click .omni_hr_attendance_sign_in_out_icon": "checker",
            "click .list_view_js": "list",
        },

        checker: function (ev) {
            ev.preventDefault();
            ajax.jsonRpc("/omni/my/attendance/update", 'call', {
            }).then(function(){
                window.location.reload();
            });
        },
        list: function(ev) {
            ev.preventDefault();
            window.location.href = '/omni/my/attendance/list_view';
        },

    });
});