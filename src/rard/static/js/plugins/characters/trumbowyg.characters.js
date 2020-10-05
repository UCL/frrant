/* ===========================================================
Provides an interface to select special characters for Antiquarian project
*/

(function ($) {
    'use strict';

    var defaultOptions = {
        characterList: [
            ['asterisk', 'Asterisk'],
            ['diple_periestigmene', 'Diple Periestigmene'],
        ]
    };

    $.extend(true, $.trumbowyg, {
        langs: {
            en: {
                characters: 'Insert Character'
            },
        },
        plugins: {
            characters: {
                init: function (trumbowyg) {
                    trumbowyg.o.plugins.characters = trumbowyg.o.plugins.characters || defaultOptions;
                    var charactersBtnDef = {
                        dropdown: buildDropdown(trumbowyg),
                        hasIcon: true,
                    };

                    trumbowyg.addBtnDef('characters', charactersBtnDef);

                    var vinculumOnBtnDef = {
                        fn: function() {
                            trumbowyg.saveRange();
                            var text = trumbowyg.getRangeText();
                            var html = '<span class="vinculum">'+text+'</span>'
                            trumbowyg.execCmd('insertHTML', html);
                        },
                        title: 'Add Vinculum',
                        text: 'V',
                        hasIcon: false,
                    }
                    var vinculumOffBtnDef = {
                        fn: function() {
                            trumbowyg.saveRange();
                            var text = trumbowyg.getRangeText();
                            var html = '<span>'+text+'</span>'
                            trumbowyg.execCmd('insertHTML', html);
                        },
                        title: 'Remove Vinculum',
                        text: 'V',
                        hasIcon: false,
                    }
                    trumbowyg.addBtnDef('vinculum_on', vinculumOnBtnDef);
                    trumbowyg.addBtnDef('vinculum_off', vinculumOffBtnDef);
                }
            }
        }
    });

    function buildDropdown(trumbowyg) {
        var dropdown = [];
        $.each(trumbowyg.o.plugins.characters.characterList, function (i, symbol_info) {
            let symbol = symbol_info[0];
            let symbol_name = symbol_info[1];            

            var btn = symbol.replace(/:/g, ''),
                defaultSymbolBtnName = 'symbol-' + btn,
                defaultSymbolBtnDef = {
                    // text: '&nbsp;',
                    text: symbol_name,
                    hasIcon: false,
                    title: symbol_name,
                    fn: function () {
                        trumbowyg.execCmd('insertHTML', '<img class="character '+symbol+'"></img>');
                        // if we need to strip auto-generated styles from the editor
                        // we can do that here
                        // $('img.character').removeAttr('style');
                        // $('span').removeAttr('style');
                        return true;
                    }
                };

            trumbowyg.addBtnDef(defaultSymbolBtnName, defaultSymbolBtnDef);
            dropdown.push(defaultSymbolBtnName);
        });

        return dropdown;
    }
})(jQuery);