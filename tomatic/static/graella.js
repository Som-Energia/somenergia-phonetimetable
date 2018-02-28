'use strict';
var m = require('mithril');

m.prop = require('mithril/stream');

var Snackbar = require('polythene-mithril-snackbar').Snackbar;
var Button = require('polythene-mithril-button').Button;
var Dialog = require('polythene-mithril-dialog').Dialog;
var Checkbox = require('polythene-mithril-checkbox').Checkbox;
var RadioGroup = require('polythene-mithril-radio-group').RadioGroup;
var RadioButton = require('polythene-mithril-radio-button').RadioButton;
var List = require('polythene-mithril-list').List;
var ListTile = require('polythene-mithril-list-tile').ListTile;
var Ripple = require('polythene-mithril-ripple').Ripple;
var Card = require('polythene-mithril-card').Card;
//var HeaderPanel = require('polythene-mithril-header-panel');
var IconButton = require('polythene-mithril-icon-button').IconButton;
var Icon = require('polythene-mithril-icon').Icon;
var Tabs = require('polythene-mithril-tabs').Tabs;
var Textfield = require('polythene-mithril-textfield').TextField;
var DatePicker = require('mithril-datepicker/mithril-datepicker')
var datePickerStyle = require('mithril-datepicker/src/style.css');


var iconMenu = require('mmsvg/google/msvg/navigation/menu');
var iconMore = require('mmsvg/google/msvg/navigation/more-vert');
var iconEdit = require('mmsvg/google/msvg/editor/mode-edit');
var iconPalette = require('mmsvg/google/msvg/image/palette');
var iconDate =  require('mmsvg/google/msvg/action/date-range');
var iconDelete =  require('mmsvg/google/msvg/action/delete');
var iconPlus =  require('mmsvg/templarian/msvg/plus');

var Tomatic = require('./components/tomatic');
var Select = require('./components/select');
var RgbEditor = require('./components/rgbeditor');
var Uploader = require('./components/uploader');
var luminance = require('./components/colorutils').luminance;

var css = require('polythene-css');
var customStyle = require('./style.styl');

css.addLayoutStyles();
css.addTypography();

var Todo = function(message) {
	return m(Card, {
		content: [{
			primary: {
				title: 'TODO',
				subtitle: message,
			},
		}],
	});
};

var Doc = function(message) {
	return m(Card, {
		content: [{
			primary: {
				title: "Info",
				subtitle: message,
			},
		}],
	});
};

var QueueWidget = {
	oninit: function(vnode) {
		vnode.state = {
			addtoqueue: function(ev) {
				Dialog.show({
					id: 'QueuePersonPicker',
					title: 'Obre una nova línia amb:',
					backdrop: true,
					body: [
						m(PersonPicker, {
							id:'QueuePersonPicker',
							onpick: function(name) {
								Dialog.hide({id: 'QueuePersonPicker'});
								Tomatic.addLine(name);
							}
						}),
					],
					footerButtons: [
						m(Button, {
							label: "Tanca",
							events: {
								onclick: function() {
									Dialog.hide({id: 'QueuePersonPicker'});
								},
							},
						}),
					],
				}, {id: 'QueuePersonPicker'});
			},
			resume: function(line, ev) {
				Tomatic.restoreLine(line);
			},
			pause: function(line, ev) {
				Tomatic.pauseLine(line);
			},
		};
	},
	view: function(vnode) {
		return m('.queueeditor',
			Tomatic.queue().map(function(line) {
				return m('.queueitem.'+line.key, {
					'class': line.paused?'paused':'resumed',
					onclick: line.paused?
						vnode.state.resume.bind(vnode.state,line.key):
						vnode.state.pause.bind(vnode.state,line.key),
					},
					Tomatic.extension(line.key)
				);
			}),
			m('.queueitem.add', {
				onclick: vnode.state.addtoqueue.bind(vnode.state),
				},
				"+"
			)
		);
	}
};
var PersonPicker = {
	oninit: function(vnode) {
		var c = {
			onpick: vnode.attrs.onpick,
			nobodyPickable: vnode.attrs.nobodyPickable,
			person: m.prop(undefined),
			picked: function(name, ev) {
				vnode.state.person(name);
				if (vnode.attrs.onpick) {
					vnode.attrs.onpick(name);
				}
			},
		};
		vnode.state=c;
	},
	view: function(vnode) {
		var pickCell = function(name) {
			return m('.extension', {
				class: name,
				onclick: vnode.state.picked.bind(vnode,name),
				},
				Tomatic.formatName(name)
			);
		};
		var extensions = Tomatic.persons().extensions || {};
		return m('.extensions', [
			Object.keys(extensions).sort().map(pickCell),
			vnode.attrs.nobodyPickable ? pickCell('ningu') : [],
		]);
	},
};

var WeekList = {
	oninit: function(vnode) {
		vnode.state = {
			model: this,
			setCurrent: function(week) {
				Tomatic.requestGrid(week);
			},
		};
	},
	view: function(c) {
		return m('.weeks',
			Tomatic.weeks().map(function(week){
				var current = Tomatic.currentWeek() === week ? '.current':'';
				return m('.week'+current, {
					onclick: function() {
						c.state.setCurrent(week);
					}
				}, "Setmana del "+week);
		}));
	}
};
const ButtonIcon = function(msvg) {
	return m(IconButton, {
		icon: {
			svg: msvg
		},
		class: 'colored',
		ink: true,
		wash: true,
	});
};

const toolbarRow = function(title) {
	return m('.pe-toolbar.flex.layout',[
		ButtonIcon(iconMenu),
		m('.flex', title),
		ButtonIcon(iconMore)
	]);
}

function nextMonday(date) {
	var d = d || new Date();
	d.setDate(d.getDate() + 14 - (6+d.getDay())%7);
	return d.toISOString().substr(0,10);
}

var BusyList = {
	view: function(vnode, attrs) {
		return m('',[
			m(List, {
				header: {
					title: m('.layout.justified.center', [
						vnode.attrs.title,
						m(IconButton, {
							icon: { svg: iconPlus, },
							compact: true,
							wash: true,
							class: 'colored',
							events: {
								onclick: function () {
									var newEntry = {
										weekday: vnode.attrs.isOneShot?undefined:'',
										date: vnode.attrs.isOneShot?nextMonday():undefined,
										reason: '',
										optional: true,
										turns: '0000',
									};
									editAvailability(newEntry, function(entry) {
										vnode.attrs.entries.push(entry);
										vnode.attrs.onChange && vnode.attrs.onChange();
									});
								},
							}
						}),
					]),
				},
				//compact: true,
				tiles: vnode.attrs.entries.map(function(entry, index) {
					var turns = Array.from(entry.turns).map(function(e) {
						return m.trust(e-0?'&#x2612;':'&#x2610;');
					});
					var day = entry.date || Tomatic.weekday(entry.weekday, 'Tots els dies');

					return m(ListTile, {
						front: m('.optionallabel',
							entry.optional?'Opcional':''),
						title: m('.layout.justified', [
							day,
							m('.turns',turns)
						]),
						subtitle: entry.reason,
						secondary: {
							content: m(IconButton, {
								icon: { svg: iconDelete },
								compact: true,
								wash: true,
								class: 'colored',
								events: {
									onclick: function() {
										vnode.attrs.entries.splice(index, 1);
										console.log(vnode.attrs.entries);
										vnode.attrs.onChange && vnode.attrs.onChange();
									},
								},
							}),
						},
						events: {
							onclick: function() {
								editAvailability(entry, function(modifiedEntry) {
									Object.assign(entry, modifiedEntry);
									vnode.attrs.onChange && vnode.attrs.onChange();
								});
							},
						},
					});
				}),
				borders: true,
				hoverable: true,
			}),
		]);
	},
};

var BusyEntryEditor = {
	oncreate: function(vnode) {
		// TODO: Focus on Motiu
		console.debug(vnode.children);
	},
	oninit: function(vnode) {
		vnode.state.busy = vnode.attrs.busy;
	},
	view: function(vnode) {
		var busy = vnode.attrs.busy;
		return m('.busyentryeditor', [
			m(Textfield, {
				label: 'Motiu',
				floatingLabel: true,
				autofocus: 1,
				help: 'Explica el motiu, com a referència',
				required: true,
				value: busy.reason,
				onChange: function(state) {
					busy.reason=state.value;
				},
			}),
			m('.pe-textfield.pe-textfield--dirty.pe-textfield--floating-label', [
				m('.pe-textfield__input-area', [
					m('label[for=optional].pe-textfield__label',
						"Opcional?"),
					m(RadioGroup, {
						name: 'optional',
						id: 'optional',
						onChange: function(state) {
							busy.optional = state.value;
						},
						className: 'layout.pe-textfield__input',
						all: {
							className: 'flex',
						},
						buttons: [
							{
								label: 'Sí',
								value: true,
								checked: busy.optional,
							},
							{
								label: 'No',
								value: false,
								checked: !busy.optional,
							},
						],
					}),
					m('.pe-textfield__help',
						"Es pot descartar si estem apurats?"),
				])
			]),
			busy.weekday !== undefined ?
				m(Select, {
					label: 'Dia de la setmana',
					value: busy.weekday,
					options: {
						'': 'Tots els dies',
						dl: 'Dilluns',
						dm: 'Dimarts',
						dx: 'Dimecres',
						dj: 'Dijous',
						dv: 'Divendres',
					},
					onChange: function(ev) {
						busy.weekday = ev.target.value;
					},
				}):[],
			/*
			busy.weekday === undefined ?
				m(Textfield, {
					label: 'Data',
					pattern: '20[0-9]{2}-[01][0-9]-[0-3][0-9]$',
					error: 'Data en format ISO YYYY-MM-DD',
					floatingLabel: true,
					help: 'Especifica la data concreta de la indisponibilitat',
					required: true,
					validate: function(value) {
						console.debug("Validating: ", value);
						if (!isNaN(Date.parse(value))) {return {valid: true};}
						return {
							valid: false,
							error: 'Data en format ISO YYYY-MM-DD',
						};
					},
					value: busy.date,
					onChange: function(state) {
						console.debug("Changing date:",busy.date, "->", state.value);
						busy.date=state.value;
					},
				}):[],
			*/
			busy.weekday === undefined ?
				m(DatePicker, {
					date: Date.parse(busy.date),
					onchange: function(newDate) {
						busy.date=newDate.toISOString().substr(0,10)+'';
						console.debug("date:",busy.date);
					},
					locale: 'ca',
					weekstart: 1,
				}):[],
			m('p.label', "Marca les hores que no estaràs disponible:"),
			Array.from(busy.turns).map(function(active, i) {
				var hours = Tomatic.grid().hours;
				return m('', m(Checkbox, {
					label: hours[i]+' - '+hours[i+1],
					checked: active==='1',
					onChange: function(state) {
						console.debug("onchange:",state);
						console.debug('Before:',busy.turns);
						busy.turns = (
							busy.turns.substr(0,i)+
							((busy.turns[i]==='1')?'0':'1')+
							busy.turns.substr(i+1)
						);
						console.debug('After:',busy.turns);
					},
				}));
			}),
		]);
	},
};

var editAvailability = function(receivedData, updateCallback) {
	var busy = Object.assign({}, receivedData);
	Dialog.show(function () { return {
		id: 'BusyEditor',
		title: 'Edita indisponibilitat',
		backdrop: true,
		body: m(BusyEntryEditor, {
			busy: busy,
		}),
		footerButtons: [
			m(Button, {
				label: "Accepta",
				events: {
					onclick: function() {
						updateCallback(busy);
						Dialog.hide({id:'BusyEditor'});
					},
				},
				disabled: !busy.reason,
			}),
			m(Button, {
				label: "Cancel·la",
				events: {
					onclick: function() {
						Dialog.hide({id:'BusyEditor'});
					},
				},
			}),
		],
	};},{id: 'BusyEditor'});
};

var editAvailabilities = function(name) {
	Tomatic.retrieveBusyData(name, function(data) {
		Dialog.show(function () { return {
			id: 'BusyListEditor',
			title: 'Edita indisponibilitats '+Tomatic.formatName(name),
			backdrop: true,
			body: [
				m('.busylist', [
					m(BusyList, {
						title: 'Setmanals',
						entries: data.weekly,
						isOneShot: false,
						onChange: function() {
							console.log("Updating data:\n",data);
							Tomatic.sendBusyData(name, data);
						},
					}),
					m(BusyList, {
						title: 'Puntuals',
						entries: data.oneshot,
						isOneShot: true,
						onChange: function() {
							console.log("Updating data:\n",data);
							Tomatic.sendBusyData(name, data);
						},
					}),
				]),
			],
			footerButtons: [
				m(Button, {
					label: "Tanca",
					events: {
						onclick: function() {
							Dialog.hide({id:'BusyListEditor'});
						},
					},
				}),
			],
		};}, {id: 'BusyListEditor'});
		//m.redraw();
	});
};

var editPerson = function(name) {
	var taulaLabel = function(n) {
		var companys = Tomatic.peopleInTable(n)
			.filter(function(item) {
				return item!==name;})
			.map(function(item) {
				return Tomatic.formatName(item);})
			.join(', ')
			;
		if (!companys) { companys = "ningú més"; }
		return "Taula "+n+": amb "+companys;
	};
	function getDataFromTomatic(name) {
		return {
			newone: (name===undefined?true:false),
			name: name,
			formatName: Tomatic.formatName(name),
			color: Tomatic.persons().colors[name],
			extension: Tomatic.persons().extensions[name],
			table: Tomatic.table(name),
		};
	};
	function setDataOnTomatic(name, data) {
		var old = getDataFromTomatic(name);
		var changed = {};
		for (var k in old) {
			if (old[k]!==data[k]) {
				changed[k]=data[k];
			}
		}
		console.log('setDataOnTomatic', name, changed);
		Tomatic.setPersonData(name, data);
	};
    function maxValue(object) {
        var keys = Object.keys(object);
        var values = keys.map(function(key) { return object[key]; })
        return Math.max.apply(null, values);
    }
    function range(n) {
        return Array.apply(null, Array(n)).map(function (_, i) {return i;});
    }

	var data = getDataFromTomatic(name);
	data.tables = {};
	var tablesToFill = range(maxValue(Tomatic.persons().tables)+2);
	tablesToFill.map(function(n) {
		data.tables[n] = taulaLabel(n);
	});
	Dialog.show(function() { return {
		title: 'Edita dades de la persona '+Tomatic.formatName(name),
		backdrop: true,
		body: [
			m(PersonEditor, data),
		],
		footerButtons: [
			m(Button, {
				label: "Accepta",
				events: {
					onclick: function() {
						setDataOnTomatic(name, data);
						Dialog.hide({id: 'PersonEditor'});
					},
				},
			}),
			m(Button, {
				label: "Cancel·la",
				events: {
					onclick: function() {
						Dialog.hide({id:'PersonEditor'});
					},
				},
			}),
		],
		didHide: function() {m.redraw();}
	};},{id:'PersonEditor'});
};

var PersonEditor = {};
PersonEditor.view = function(vnode) {
	vnode.state.name = vnode.attrs.name;
	return m('.personEditor', [
		m(Textfield, {
			label: 'Identificador',
			floatingLabel: true,
			pattern: '[a-z]{3,10}$',
			help: 'Identificador que es fa servir internament.',
			error: 'De 3 a 10 carácters. Només lletres en minúscules.',
			required: true,
			disabled: !vnode.attrs.newone,
			value: vnode.attrs.name || '',
			onChange: function(state) {
				vnode.attrs.name=state.value;
			},
		}),
		m(Textfield, {
			label: 'Nom mostrat',
			floatingLabel: true,
			help: 'Nom amb accents, majúscules...',
			required: true,
			value: vnode.attrs.formatName,
			onChange: function(state) {
				vnode.attrs.formatName=state.value;
			},
		}),
		m(Textfield, {
			label: 'Extensio',
			type: 'number',
			pattern: '[0-9]{4}$',
			floatingLabel: true,
			help: 'Extensió del telèfon',
			required: true,
			value: vnode.attrs.extension,
			onChange: function(state) {
				vnode.attrs.extension=state.value;
			},
		}),
		m(Select, {
			label: 'Taula',
			value: vnode.attrs.table,
			options: Object.keys(vnode.attrs.tables).reduce(function(d, k) {
				d[k] = vnode.attrs.tables[k];
				return d;
			}, { "-1": "Sense taula" }),
			onChange: function(ev) {
				vnode.attrs.table = ev.target.value;
			},
		}),
		m(
			'.pe-textfield'+
			'.pe-textfield--floating-label'+
			'.pe-textfield--hide-clear'+
			'.pe-textfield--dirty', [
			m('.pe-textfield__input-area', [
				m('label.pe-textfield__label', 'Color'),
				m(RgbEditor, {
					value: vnode.attrs.color || 'ffffff',
					onChange: function(state) {
						vnode.attrs.color = state.value;
					},
				}),
			]),
		]),
	]);
};

var Grid = function(grid) {
	var editCell = function(day, houri, turni) {
		var setPerson = function(name) {
			Tomatic.editCell(day, houri, turni, name)
			Dialog.hide({id:'GridCellEditor'});
		};
		var oldPerson = Tomatic.cell(day,houri,turni);
		Dialog.show({
			id: 'GridCellEditor',
			title: 'Edita posició de la graella',
			backdrop: true,
			body: [
				Tomatic.weekday(day) +' a les '+
					Tomatic.grid().hours[houri] +
					', línia '+ (turni+1) +
					', la feia ',
				m('span.extension.'+oldPerson, Tomatic.formatName(oldPerson)),
				' qui ho ha de fer?',
				m(PersonPicker, {
					id:'GridCellEditor',
					onpick: setPerson,
					nobodyPickable: true,
				}),
			],
			footerButtons: [
				m(Button, {
					label: "Cancel·la",
					events: {
						onclick: function() {
							Dialog.hide({id:'GridCellEditor'});
						},
					},
				}),
			],
		},{id:'GridCellEditor'});
	};
	var cell = function(day, houri, turni) {
		var name = Tomatic.cell(day,houri,turni);
		return m('td', {
			class: name||'ningu',
			onclick: function(ev) {
				editCell(day, houri, turni);
				ev.preventDefault();
			}
		}, [
			Tomatic.formatName(name),
			Tomatic.persons().extensions[name]?
				m('.tooltip', Tomatic.persons().extensions[name]):
				[],
			m(Ripple),
		]);
	};
 	return [
		(grid.days||[]).map(function(day, dayi) {
			return m('.graella', m('table', [
				m('tr', [
					m('td'),
					m('th', {colspan:grid.turns.length}, Tomatic.weekday(day)),
				]),
				m('td'),
				grid.turns.map(function(turn) {
					return m('th', turn);
				}),
				grid.hours.slice(0,-1).map(function(hour,houri) {
					return m('tr', [
						dayi!=0 && false?
							m('th.separator', m.trust('&nbsp;')) :
							m('th.separator', grid.hours[houri]+'-'+grid.hours[houri+1]),
						grid.turns.map(function(turn, turni) {
							return cell(day, houri, turni)
						}),
					]);
				}),
			]))
		}),
	];
};

var Persons = function(extensions) {
	return [
		m('.extensions', [
			Object.keys(extensions || {}).sort().map(function(name) {
				return m('.extension', {
					class: name,
					_onclick: function() {
						editPerson(name);
					},
				}, [
					Tomatic.formatName(name),
					m('br'),
					Tomatic.persons().extensions[name],
					m('.tooltip', [
						m(IconButton, {
							icon: { svg: iconDate },
							compact: true,
							wash: true,
							class: 'colored',
							events: {
							onclick: function() { editAvailabilities(name); },
							},
						}),
						m(IconButton, {
							icon: { svg: iconEdit },
							compact: true,
							wash: true,
							class: 'colored',
							events: {
							onclick: function() { editPerson(name); },
							},
						}),
					]),
					//m(Ripple),
				]);
			}),
			m('.extension.add', {
				onclick: function() {
					editPerson();
				},
			}, [
				'nova', m('br'), 'persona',
			]),
		]),
	];
};
var Extensions = function(extensions) {
	return [
		m('.extensions',
			Object.keys(extensions || {}).sort().map(function(name) {
				return m('.extension', {class: name}, [
					Tomatic.formatName(name),
					m('br'),
					extensions[name],
				]);
			})
		),
	];
};
var Forwardings = function() {
	return m('.graella', [
		m('h5', 'Codis desviaments'),
		m('ul.codes', [
			m('li','*60 Immediat'),
			m('li','*63 Ocupat o no responem'),
			m('li','*64 Treure desviaments'),
			m('li','*90 Marcar número'),
		]),
	]);
};
var Changelog = function(grid) {
	return m('.graella', [
		m('h5', 'Darrers canvis'),
		m('ul.changelog', [
			grid.log?[]: m('li', 'Cap canvi registrat'),
			(grid.log || []).slice(-5).reverse().map(function(change) {
				return m('li',change);
			}),
			(grid.log || []).length > 5 ?  m('li', m.trust("&hellip;")) : [],
		]),
	]);
};
var Penalties = function(grid) {
	return m('.graella', [
		m('h5', 'Penalitzacions (', grid.cost || 0, ' punts)'),
		m('ul.penalties', [
			grid.penalties?[]: m('li', 'La graella no te penalitzacions'),
			(grid.penalties || []).map(function(penalty) {
				return m('li',penalty[0],': ',penalty[1]);
			}),
		]),
	]);
};

var GridsPage = {
    view: function() {
        var grid = Tomatic.grid();
        return m('',[
			m('.layout.vertical', [
				m(WeekList),
				m('.layout.end-justified', [
					m(Uploader, {
						name: 'yaml',
						label: 'Puja Nova Graella',
						url: 'api/graella',
						onupload: function(result) {
							Tomatic.init();
						},
						onerror: function(error) {
							console.log("Upload error:", error);
							Tomatic.error("Upload error: " + error.error);
						},
					}),
				]),
			]),
			m('.layout.center-center.wrap', Grid(grid)),
			Extensions(grid.otherextensions),
			m('.layout.around-justified.wrap', [
				Forwardings(),
				Changelog(grid),
				Penalties(grid),
			]),
        ]);
    },
};

var PbxPage = {
    view: function() {
        return m('', [
			Doc([
				m('',
				"Visualitza les línies que estan actualment rebent trucades. "+
				"Feu click al damunt per pausar-les o al signe '+' per afegir-ne"),
				m('b','Les accions no tenen efecte sense la centraleta nova.'),
				]),
			m('h2[style=text-align:center]', "Linies en cua"),
			m(QueueWidget),
        ]);
    },
};

var PersonsPage = {
    view: function() {
        return m('', [
			Doc("Permet modificar la configuració personal de cadascú: "+
				"Color, taula, extensió e indisponibilitats."),
			Persons(Tomatic.persons().extensions),
        ]);
    },
};

var CallInfoPage = {
    view: function() {
        return m('',[
			Todo(
				"Aquí es podrà veure informació de l'ERP sobre la trucada entrant"
            ),
        ]);
    },
};

var PersonStyles = function() {
	var persons = Tomatic.persons();
    return m('style',
        Object.keys(persons.colors||{}).map(function(name) {
            var color = '#'+persons.colors[name];
            var darker = '#'+luminance(color, -0.3);
            return (
                '.'+name+', .graella .'+name+' {\n' +
                '  background-color: '+color+';\n' +
                '  border-color: '+darker+';\n' +
                '  border-width: 2pt;\n'+
                '}\n'+
                '.pe-dark-theme .'+name+', .pe-dark-theme .graella .'+name+' {\n' +
                '  background-color: '+darker+';\n' +
                '  border-color: '+color+';\n' +
                '  border-width: 2pt;\n'+
                '}\n');
        })
    );
};

const applicationPages = [
	"Graelles",
	"Centraleta",
	"Persones",
	"Trucada",
	];

var tabs = applicationPages.map(function(name) {
    return {
        label: name,
        url: {
            oncreate: m.route.link,
            href: '/'+name
        },
    };
});
const indexForRoute = function(route) {
    return tabs.reduce(function(previousValue, tab, index) {
        if (route === tab.url.href) {
            return index;
        } else {
            return previousValue;
        }
    }, 0);
};


var Page = {};
Page.view = function(vnode) {
    var currentTabIndex = indexForRoute(m.route.get());
	return m('', [
		m('.tmt-header', [
			m('.tmt-header__dimmer'),
            toolbarRow('Tomàtic - Som Energia'),
			m(Tabs, {
				tabs: tabs,
				//centered: true,
				activeSelected: true,
				//hideIndicator: true,
				selectedTab: currentTabIndex,
			}),
		]),
		vnode.attrs.content,
		m('#snackbar',m(Snackbar)),
		m(Dialog),
	]);
		
};


var TomaticApp = {}
TomaticApp.view = function() {
    var pages = {
        'Graelles': GridsPage,
        'Centraleta': PbxPage,
        'Persones': PersonsPage,
        'Trucada': CallInfoPage,
    };
	console.log("Page: ", m.route.get());
    var currentTabIndex = indexForRoute(m.route.get());
    var current = m(pages[tabs[currentTabIndex].label]);
    return m('',[
        PersonStyles(),
        m(Page, {content:current}),
    ]);
};



window.onload = function() {
	Tomatic.init();
    //m.redraw.strategy('diff');
	var element = document.getElementById("tomatic");
	m.route(element, '/Graelles', {
        '/Graelles': TomaticApp,
        '/Centraleta': TomaticApp,
        '/Persones': TomaticApp,
        '/Trucada': TomaticApp,
    });
};
// vim: noet ts=4 sw=4
