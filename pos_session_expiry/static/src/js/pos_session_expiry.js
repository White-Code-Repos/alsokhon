odoo.define('pos_session_expiry.pos_session_expiry', function (require) {
    "use strict";

    var rpc = require('web.rpc');
    var gui = require('point_of_sale.gui');

    var inactivityTime = function (gui, session_expiry_seconds) {

        var idel_time;
        var log_msg = "Note: auto close session initiation after " +
            session_expiry_seconds +
            " idle seconds";
        console.log(log_msg);
        var msg = "The session is idle more than " +
            session_expiry_seconds +
            " seconds, the session will close automatically.";
        if (session_expiry_seconds > 0) {
            window.onload = resetTimer;
            document.onmousemove = resetTimer;
            document.onkeypress = resetTimer;

            function logout() {
                console.log(msg);
                // alert(msg);
                gui.close();
            }

            function resetTimer() {
                clearTimeout(idel_time);
                idel_time = setTimeout(logout, session_expiry_seconds * 1000);
            }
        }
    };

    gui.Gui.include({
        init: function (options) {
            var self = this;
            this._super(options);
            var session_expiry_seconds = 0;
            rpc.query({
                model: 'pos.config',
                method: 'read',
                args: [[this.pos.config_id], ['session_expiry_seconds']]
            }).then(function (config) {
                session_expiry_seconds = config[0]['session_expiry_seconds'];
                if (session_expiry_seconds) {
                    inactivityTime(self, session_expiry_seconds);
                }
            });
        },
    });
});
