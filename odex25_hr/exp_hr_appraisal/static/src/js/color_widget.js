odoo.define('exp_hr_appraisal.color_widget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');
    var QWeb = core.qweb;  // Load QWeb templates

    var ColorWidget = AbstractField.extend({
        className: 'o_color_widget',
        supportedFieldTypes: ['selection'],  // Works with selection field
        events: {
            'click .o_color_option': '_onColorClick',
        },

        // Render the widget
        _render: function () {
            this.$el.empty();  // Clear the element

            var colors = [
                { value: 'red', label: 'Red' },
                { value: 'blue', label: 'Blue' },
                { value: 'green', label: 'Green' },
                { value: 'orange', label: 'Orange' },
                { value: 'purple', label: 'Purple' },
            ];

            // Check if the template is loaded
            if (!QWeb.has_template('ColorWidgetOptions')) {
                console.error("QWeb template 'ColorWidgetOptions' not found!");
                return;
            }

            // Render the color picker using QWeb
            this.$el.append(QWeb.render('ColorWidgetOptions', {
                colors: colors,
                selectedColor: this.value || 'blue',  // Default to 'blue'
            }));
        },

        // Handle color selection
        _onColorClick: function (ev) {
            var selectedColor = $(ev.currentTarget).data('color');  // Get selected color
            this._setValue(selectedColor);  // Set selection field value
            this._render();  // Re-render widget to update UI
        },
    });

    // Register widget
    fieldRegistry.add('color_widget', ColorWidget);

    return {
        ColorWidget: ColorWidget,
    };
});
