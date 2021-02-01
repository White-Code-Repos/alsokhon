odoo.define('gold_position.GoldReportListView', function (require) {
"use strict";

var ListView = require('web.ListView');
var GoldReportListController = require('gold_position.GoldReportListController');
var viewRegistry = require('web.view_registry');


var GoldReportListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: GoldReportListController,
    }),
});

viewRegistry.add('gold_fixing_position_report_list', GoldReportListView);

return GoldReportListView;

});
