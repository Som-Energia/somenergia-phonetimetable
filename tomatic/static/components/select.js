'use strict';
module.exports = function() {

    var m = require('mithril');

	m.prop = require('mithril/stream');

    var Select = {
		oninit: function(vnode) {
			vnode.state.value = m.prop(vnode.attrs.value);
		},
        view: function(vnode) {
            return m('.pe-textfield.pe-textfield--floating-label'+
                    '.pe-textfield--hide-clear.pe-textfield--dirty', [
                m('.pe-textfield__input-area', [
                    m('label.pe-textfield__label', vnode.attrs.label),
                    m('select.pe-textfield__input', {
                        value: vnode.state.value(),
                        onchange: function(ev) {
                            vnode.state.value(ev.target.value);
                            vnode.attrs.onChange(ev);
                        },
                    },
                    Object.keys(vnode.attrs.options).map(function(value) {
                        return m('option', {
                            value: value,
                        }, vnode.attrs.options[value]);
                    })),
                ]),
            ]);
        },
    };

	return Select;
}();

// vim: noet ts=4 sw=4
