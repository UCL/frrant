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
                            console.log('range text is '+text);
                            let html = '';
                            for (let i = 0; i < text.length; i++) {
                                console.log('character '+text[i]);
                                html += text[i] + '\u0305'
                            }
                            trumbowyg.execCmd('insertHTML', html);
                        },
                        title: 'Add Vinculum',
                        text: 'V',
                        hasIcon: false,
                    }
                    var vinculumOffBtnDef = {
                        fn: function() {
                            trumbowyg.saveRange();
                            let html = ''
                            var text = trumbowyg.getRangeText();
                            for (let i=0; i < text.length; i++) {
                                console.log('text is '+text[i]);
                                if (text[i] != '\u0305') {
                                    html += text[i];
                                }
                            }
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
                    text: symbol_name,
                    hasIcon: false,
                    title: symbol_name,
                    fn: function () {
                        trumbowyg.execCmd('insertHTML', '<img class="character '+symbol+'"></img>');
                        return true;
                    }
                };

            trumbowyg.addBtnDef(defaultSymbolBtnName, defaultSymbolBtnDef);
            dropdown.push(defaultSymbolBtnName);
        });

        return dropdown;
    }
})(jQuery);
