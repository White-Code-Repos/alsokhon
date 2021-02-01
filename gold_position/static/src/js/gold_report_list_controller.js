odoo.define('gold_position.GoldReportListController', function (require) {
"use strict";

var core = require('web.core');
var ListController = require('web.ListController');

var qweb = core.qweb;


var GoldReportListController = ListController.extend({

    // -------------------------------------------------------------------------
    // Public
    // -------------------------------------------------------------------------

    init: function (parent, model, renderer, params) {
        this.context = renderer.state.getContext();
        return this._super.apply(this, arguments);
    },

    /**
     * @override
     */
    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        if (this.context.no_at_date) {
            return;
        }
        var $buttonToDate = $(qweb.render('GoldReport.Buttons'));
        $buttonToDate.on('click', this._onOpenWizard.bind(this));

        $buttonToDate.prependTo($node.find('.o_list_buttons'));

        var $button = $(qweb.render('GoldFixingReport.Buttons'));
        $button.on('click', this._onOpenView.bind(this));

        $button.prependTo($node.find('.o_list_buttons'));
    },

    // -------------------------------------------------------------------------
    // Handlers
    // -------------------------------------------------------------------------

    /**
     * Handler called when the user clicked on the 'Inventory at Date' button.
     * Opens wizard to display, at choice, the products inventory or a computed
     * inventory at a given date.
     */
    _onOpenWizard: function () {
        var state = this.model.get(this.handle, {raw: true});
        var stateContext = state.getContext();
        var context = {
            active_model: this.modelName,
        };
        this._rpc({
            model: 'gold.fixing.position.wizard',
            method: 'action_confirm',
            args: [[]],
        }).then(function (result) {
            return 1;
        });
    },
    _onOpenView: function () {
        var state = this.model.get(this.handle, {raw: true});
        var stateContext = state.getContext();
        var context = {
            active_model: this.modelName,
        };
         this.do_action({
                name: "Gold Fixing Position",
                type: 'ir.actions.act_window',
                res_model: 'gold.fixing.position',
                views: [[false, 'form']],
                target: 'new',
                flags: {mode:'readonly'},
            });
    },
});

return GoldReportListController;

});
