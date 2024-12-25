odoo.define('fims_row_no_header_fix_tree_view.list_search', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        events: _.extend({
            'keyup .oe_search_input': '_onKeyUp'
        }, ListRenderer.prototype.events),
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.$('.o_list_table').addClass('o_list_table_ungrouped');
                if (self.arch.tag == 'tree' && self.$el.hasClass('o_list_view')) {
                    // Check if the search input already exists
                    if (!self.$el.find('.oe_search_input').length) {
                        var search = '<input type="text" class="oe_search_input mt-2 ml-2 pl-3" placeholder="Search...">';
                        self.$el.find('table').addClass('oe_table_search');
                        var $search = $(search).css('border', '1px solid #ccc')
                            .css('width', '99%')
                            .css('height', '28px')
                        self.$el.prepend($search);
                    }
                }
            });
        },
        _onKeyUp: function (event) {
            var value = $(event.currentTarget).val().toLowerCase();
            var count_row = 0;
            var $el = $(this.$el)
            $(".oe_table_search tr:not(:first)").filter(function() {
                $(this).toggle(arabicCaseInsensitiveSearch($(this).text(),value))
                count_row = arabicCaseInsensitiveSearch($(this).text(),value) ? count_row+1 : count_row
            });
        },
    });

    function normalizeArabic(text) {
        // Normalizing Arabic text by removing common variations
        return text
            .replace(/[\u064B-\u065F]/g, '') // Remove diacritics
            .replace(/[\u0660-\u0669]/g, (d) => String.fromCharCode(d.charCodeAt(0) - 0x0660 + 0x0030)) // Convert Arabic-Indic digits to Latin digits
            .replace(/[\u06F0-\u06F9]/g, (d) => String.fromCharCode(d.charCodeAt(0) - 0x06F0 + 0x0030)) // Convert Extended Arabic-Indic digits to Latin digits
            .replace(/[\u0622\u0623\u0625\u0627]/g, 'ا') // Normalize different forms of Alef
            .replace(/[\u0629]/g, 'ه') // Normalize Teh Marbuta to Heh
            .replace(/[\u064A\u0626\u0649]/g, 'ي') // Normalize different forms of Yeh
            .replace(/[\u0624\u0648]/g, 'و'); // Normalize Waw and its variants
    }
    
    function arabicCaseInsensitiveSearch(text, searchTerm) {
        const normalizedText = normalizeArabic(text).toLowerCase();
        const normalizedSearchTerm = normalizeArabic(searchTerm).toLowerCase();
        return normalizedText.indexOf(normalizedSearchTerm) > -1;
    }

});
