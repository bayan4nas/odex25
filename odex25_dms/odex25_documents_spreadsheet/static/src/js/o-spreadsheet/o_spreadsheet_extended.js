odoo.define("odex25_documents_spreadsheet.spreadsheet_extended", function (require) {

    const spreadsheet = require("odex25_documents_spreadsheet.spreadsheet");
    const PivotPlugin = require("odex25_documents_spreadsheet.PivotPlugin");
    const FiltersPlugin = require("odex25_documents_spreadsheet.FiltersPlugin");
    const pluginRegistry = spreadsheet.registries.pluginRegistry;

    pluginRegistry.add("odooPivotPlugin", PivotPlugin);
    pluginRegistry.add("odooFiltersPlugin", FiltersPlugin);

    return spreadsheet;
});
