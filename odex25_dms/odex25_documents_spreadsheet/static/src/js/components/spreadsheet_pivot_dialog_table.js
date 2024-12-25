odoo.define("odex25_documents_spreadsheet.PivotDialogTable", function (require) {
    "use strict";

    class PivotDialogTable extends owl.Component {
        _onCellClicked(formula) {
            this.trigger('cell-selected', { formula });
        }
    }
    PivotDialogTable.template = "odex25_documents_spreadsheet.PivotDialogTable";
    return PivotDialogTable;
});
