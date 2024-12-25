odoo.define('trahum_website_theme.menu', function (require) {
    "use strict";

    var concurrency = require('web.concurrency');
    var config = require('web.config');
    var core = require('web.core');
    var dom = require('web.dom');
    var _t = core._t;

    dom.initAutoMoreMenu = function ($el, options) {
        /**
         * Creates an automatic 'more' dropdown-menu for a set of navbar items.
         *
         * @param {jQuery} $el
         * @param {Object} [options]
         * @param {string} [options.unfoldable='none']
         * @param {function} [options.maxWidth]
         * @param {string} [options.sizeClass='SM']
         */
            options = _.extend({
                unfoldable: 'none',
                maxWidth: false,
                sizeClass: 'SM',
            }, options || {});

            var autoMarginLeftRegex = /\bm[lx]?(?:-(?:sm|md|lg|xl))?-auto\b/;
            var autoMarginRightRegex = /\bm[rx]?(?:-(?:sm|md|lg|xl))?-auto\b/;

            var $extraItemsToggle = null;

            var debouncedAdapt = _.debounce(_adapt, 250);
            core.bus.on('resize', null, debouncedAdapt);
            _adapt();

            $el.data('dom:autoMoreMenu:adapt', _adapt);
            $el.data('dom:autoMoreMenu:destroy', function () {
                _restore();
                core.bus.off('resize', null, debouncedAdapt);
                $el.removeData(['dom:autoMoreMenu:destroy', 'dom:autoMoreMenu:adapt']);
            });

            function _restore() {
                if ($extraItemsToggle === null) {
                    return;
                }
                var $items = $extraItemsToggle.children('.dropdown-menu').children();
                $items.addClass('nav-item');
                $items.children('.dropdown-item, a').removeClass('dropdown-item').addClass('nav-link');
                $items.insertBefore($extraItemsToggle);
                $extraItemsToggle.remove();
                $extraItemsToggle = null;
            }

            function _adapt() {
                _restore();

                if (!$el.is(':visible') || $el.closest('.show').length) {
                    // Never transform the menu when it is not visible yet or if
                    // it is a toggleable one.
                    return;
                }
                if (config.device.size_class <= config.device.SIZES[options.sizeClass]) {
                    return;
                }

                var $allItems = $el.children();
                var $unfoldableItems = $allItems.filter(options.unfoldable);
                var $items = $allItems.not($unfoldableItems);

                var maxWidth = 0;
                if (options.maxWidth) {
                    maxWidth = options.maxWidth();
                } else {
                    maxWidth = computeFloatOuterWidthWithMargins($el[0], true, true, true);
                    var style = window.getComputedStyle($el[0]);
                    maxWidth -= (parseFloat(style.paddingLeft) + parseFloat(style.paddingRight) + parseFloat(style.borderLeftWidth) + parseFloat(style.borderRightWidth));
                    maxWidth -= _.reduce($unfoldableItems, function (sum, el) {
                        return sum + computeFloatOuterWidthWithMargins(el, true, true, false);
                    }, 0);
                }

                var nbItems = $items.length;
                var menuItemsWidth = _.reduce($items, function (sum, el) {
                    return sum + computeFloatOuterWidthWithMargins(el, false, false, false);
                }, 0);

                if (maxWidth - menuItemsWidth >= -0.001) {
                    return;
                }

                maxWidth = maxWidth - 130

                var $dropdownMenu = $('<ul/>', {
                    class: 'dropdown-menu'
                });
                $extraItemsToggle = $('<li/>', {
                        class: 'nav-item dropdown o_extra_menu_items'
                    })
                    .append($('<a/>', {
                            role: 'button',
                            href: '#',
                            class: 'nav-link dropdown-toggle o-no-caret',
                            'data-toggle': 'dropdown',
                            'aria-expanded': false
                        })
                        .append($('<i/>', {
                            class: 'fa fa-plus'
                        })))
                    .append($dropdownMenu);
                $extraItemsToggle.insertAfter($items.last());

                menuItemsWidth += computeFloatOuterWidthWithMargins($extraItemsToggle[0], true, true, false);
                do {
                    menuItemsWidth -= computeFloatOuterWidthWithMargins($items.eq(--nbItems)[0], true, true, false);
                } while (!(maxWidth - menuItemsWidth >= -0.001) && (nbItems > 0));

                var $extraItems = $items.slice(nbItems).detach();
                $extraItems.removeClass('nav-item');
                $extraItems.children('.nav-link, a').removeClass('nav-link').addClass('dropdown-item');
                $dropdownMenu.append($extraItems);
                $extraItemsToggle.find('.nav-link').toggleClass('active', $extraItems.children().hasClass('active'));
            }

            function computeFloatOuterWidthWithMargins(el, mLeft, mRight, considerAutoMargins) {
                var rect = el.getBoundingClientRect();
                var style = window.getComputedStyle(el);
                var outerWidth = rect.right - rect.left;
                if (mLeft !== false && (considerAutoMargins || !autoMarginLeftRegex.test(el.getAttribute('class')))) {
                    outerWidth += parseFloat(style.marginLeft);
                }
                if (mRight !== false && (considerAutoMargins || !autoMarginRightRegex.test(el.getAttribute('class')))) {
                    outerWidth += parseFloat(style.marginRight);
                }
                // Would be NaN for invisible elements for example
                return isNaN(outerWidth) ? 0 : outerWidth;
            }
    };

    return dom;
});