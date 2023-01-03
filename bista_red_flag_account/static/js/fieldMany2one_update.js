odoo.define('bista_red_flag_account.fieldMany2one_update', function (require) {
    'use strict';

    var core = require('web.core');
    var data = require('web.data');
    const { sprintf, toBoolElse } = require("web.utils");
    
    const { escape } = owl.utils;
    var _t = core._t;

    var FieldMany2One = require('web.relational_fields').FieldMany2One;
    FieldMany2One.include({
        /**
         * @private
         */
        _bindAutoComplete: function () {
            var self = this;
            // avoid ignoring autocomplete="off" by obfuscating placeholder, see #30439
            if ($.browser.chrome && this.$input.attr('placeholder')) {
                this.$input.attr('placeholder', function (index, val) {
                    return val.split('').join('\ufeff');
                });
            }
            this.$input.autocomplete({
                source: function (req, resp) {
                    self.suggestions = [];
                    _.each(self._autocompleteSources, function (source) {
                        // Resets the results for this source
                        source.results = [];

                        // Check if this source should be used for the searched term
                        const search = req.term.trim();
                        if (!source.validation || source.validation.call(self, search)) {
                            source.loading = true;

                            // Wrap the returned value of the source.method with a promise
                            // So event if the returned value is not async, it will work
                            Promise.resolve(source.method.call(self, search)).then(function (results) {
                                source.results = results;
                                source.loading = false;
                                self.suggestions = self._concatenateAutocompleteResults();
                                resp(self.suggestions);
                            });
                        }
                    });
                },
                select: function (event, ui) {
                    // do not select anything if the input is empty and the user
                    // presses Tab (except if he manually highlighted an item with
                    // up/down keys)
                    if (!self.floating && event.key === "Tab" && self.ignoreTabSelect) {
                        return false;
                    }

                    if (event.key === "Enter") {
                        // on Enter we do not want any additional effect, such as
                        // navigating to another field
                        event.stopImmediatePropagation();
                        event.preventDefault();
                    }

                    var item = ui.item;
                    self.floating = false;
                    if (item.id) {
                        self.reinitialize({id: item.id, display_name: item.name});
                    } else if (item.action) {
                        item.action();
                    }
                    return false;
                },
                focus: function (event) {
                    event.preventDefault(); // don't automatically select values on focus
                    if (event.key === "ArrowUp" || event.key === "ArrowDown") {
                        // the user manually selected an item by pressing up/down keys,
                        // so select this item if he presses tab later on
                        self.ignoreTabSelect = false;
                    }
                },
                open: function (event) {
                    self._onScroll = function (ev) {
                        if (ev.target !== self.$input.get(0) && self.$input.hasClass('ui-autocomplete-input')) {
                            if (ev.target.id === self.$input.autocomplete('widget').get(0).id) {
                                ev.stopPropagation();
                                return;
                            }
                            self.$input.autocomplete('close');
                        }
                    };
                    window.addEventListener('scroll', self._onScroll, true);
                },
                close: function (event) {
                    self.ignoreTabSelect = false;
                    // it is necessary to prevent ESC key from propagating to field
                    // root, to prevent unwanted discard operations.
                    if (event.which === $.ui.keyCode.ESCAPE) {
                        event.stopPropagation();
                    }
                    if (self._onScroll) {
                        window.removeEventListener('scroll', self._onScroll, true);
                    }
                },
                autoFocus: true,
                html: true,
                minLength: 0,
                delay: this.AUTOCOMPLETE_DELAY,
                classes: {
                    "ui-autocomplete": "dropdown-menu",
                },
                create: function() {
                    $(this).data('ui-autocomplete')._renderMenu = function(ulWrapper, entries) {
                    var render = this;
                    $.each(entries, function(index, entry) {
                        console.log("11111111111111111111111111111", entry)
                        render._renderItemData(ulWrapper, entry);
                    });
                    $('ul li > a').each(function(index1, entry) {
                        // $.each(entry, function(index , e1){
                            $.each(entries, function(index2, entry1) {
                                if(entry1.name == entry.innerHTML && entry1.is_blacklisted){
                                    console.log(entry1 , "22222222222222222222222222",entry.innerHTML)
                                    $(entry).addClass( "dropdown-item ui-menu-item-wrapper1" );
                                }
                            });
                        // })
                    });
                    console.log("xxxxxxxxxxxxxxxxxxx", ulWrapper)
                    $(ulWrapper).find( "li > a" ).addClass( "dropdown-item" );
                    }
                },
            });
            this.$input.autocomplete("option", "position", { my : "left top", at: "left bottom" });
            this.autocomplete_bound = true;
        },
        _search: async function (searchValue = "") {
            const value = searchValue.trim();
            const domain = this.record.getDomain(this.recordParams);
            const context = Object.assign(
                this.record.getContext(this.recordParams),
                this.additionalContext
            );
    
            // Exclude black-listed ids from the domain
            const blackListedIds = this._getSearchBlacklist();
            if (blackListedIds.length) {
                domain.push(['id', 'not in', blackListedIds]);
            }
    
            if (this.lastNameSearch) {
                this.lastNameSearch.abort(false)
            }
            this.lastNameSearch = this._rpc({
                model: this.field.relation,
                method: "name_search",
                kwargs: {
                    name: value,
                    args: domain,
                    operator: "ilike",
                    limit: this.limit + 1,
                    context,
                }
            });
            const results = await this.orderer.add(this.lastNameSearch);
    
            // Format results to fit the options dropdown
            let values = results.map((result) => {
                const [id, fullName] = result;
                const displayName = this._getDisplayName(fullName).trim();
                result[1] = displayName;
                var is_blacklisted = false
                if(result.length == 3){
                    is_blacklisted = result[2]                
                }
                console.log(result,"aaaaaaaaaaaaaaaaaaaaaaaaaa", id , displayName , data.noDisplayContent , is_blacklisted)
                return {
                    id,
                    label: escape(displayName) || data.noDisplayContent,
                    value: displayName,
                    name: displayName,
                    is_blacklisted : is_blacklisted
                };
            });
    
            // Add "Search more..." option if results count is higher than the limit
            if (this.limit < values.length) {
                values = this._manageSearchMore(values, value, domain, context);
            }
    
            // Additional options...
            const canQuickCreate = this.can_create && !this.nodeOptions.no_quick_create;
            const canCreateEdit = this.can_create && !this.nodeOptions.no_create_edit;
            if (value.length) {
                // "Quick create" option
                const nameExists = results.some((result) => result[1] === value);
                if (canQuickCreate && !nameExists) {
                    values.push({
                        label: sprintf(
                            _t(`Create "<strong>%s</strong>"`),
                            escape(value)
                        ),
                        action: () => this._quickCreate(value),
                        classname: 'o_m2o_dropdown_option'
                    });
                }
                // "Create and Edit" option
                if (canCreateEdit) {
                    const valueContext = this._createContext(value);
                    values.push({
                        label: _t("Create and Edit..."),
                        action: () => {
                            // Input value is cleared and the form popup opens
                            this.el.querySelector(':scope input').value = "";
                            return this._searchCreatePopup('form', false, valueContext);
                        },
                        classname: 'o_m2o_dropdown_option',
                    });
                }
                // "No results" option
                if (!values.length) {
                    values.push({
                        label: _t("No records"),
                        classname: 'o_m2o_no_result',
                    });
                }
            } else if (!this.value && (canQuickCreate || canCreateEdit)) {
                // "Start typing" option
                values.push({
                    label: _t("Start typing..."),
                    classname: 'o_m2o_start_typing',
                });
            }
    
            return values;
        },
    });

});