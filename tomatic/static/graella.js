'use strict';
var m = require('mithril');
require('polythene/theme/theme');
var SnackBar = require('polythene/notification/snackbar');
var Button = require('polythene/button/button');
var Dialog = require('polythene/dialog/dialog');
var Ripple = require('polythene/ripple/ripple');
var Card = require('polythene/card/card');
var HeaderPanel = require('polythene/header-panel/header-panel');
var IconButton = require('polythene/icon-button/icon-button');
var Tabs = require('polythene/tabs/tabs');
//var iconMenu = require('mmsvg/google/msvg/navigation/menu');
var iconMenu = m.trust('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>');
//var iconMore = require('mmsvg/google/msvg/navigation/more-vert');
var iconMore = m.trust('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>');

const applicationPages = [
	"Graelles",
	"Centraleta",
	"Persones",
	"Trucada",
	].map(function(n) {return {label:n};});


function hex2triplet(hex) {
	hex = String(hex).replace(/[^0-9a-f]/gi, '');
	if (hex.length < 6) {
		hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
	}
	return [
		hex.substr(0,2),
		hex.substr(2,2),
		hex.substr(4,2)
		].map(function(part) {
			return parseInt(part, 16);
		});
}
function triplet2hex(triplet) {
	var rgb = "#";
	for (let i in triplet) {
		let c = triplet[i];
		let newc = Math.round(Math.min(Math.max(0, c), 255));
		rgb += ("00"+newc.toString(16)).slice(-2);
	}
	return rgb;
}

function luminance(hex, lum) {
	var triplet = hex2triplet(hex);
	lum = lum || 0;
	return triplet2hex(triplet.map(function(c) {
		return c + c*lum;
	}))
}


var Tomatic = {
};

Tomatic.queue = m.prop([]);
Tomatic.init = function() {
	this.requestWeeks();
	this.requestQueue();
};
Tomatic.requestQueue = function(suffix) {
	m.request({
		method: 'GET',
		url: 'queue'+(suffix||''),
		deserialize: jsyaml.load,
	}).then(function(response){
		if (response.currentQueue!==undefined) {
			Tomatic.queue(response.currentQueue);
		}
	});
};

Tomatic.addLine = function(line) {
	Tomatic.requestQueue('/add/'+line);
};

Tomatic.pauseLine = function(line) {
	Tomatic.requestQueue('/pause/'+line);
};

Tomatic.restoreLine = function(line) {
	Tomatic.requestQueue('/resume/'+line);
};

Tomatic.grid = m.prop({});

Tomatic.requestGrid = function(week) {
	m.request({
		method: 'GET',
		url: 'graella-'+week+'.yaml',
		deserialize: jsyaml.load,
	}).then(function(data) {
		data.days = data.days || 'dl dm dx dj dv'.split(' ');
		Tomatic.currentWeek(week);
		Tomatic.grid(data);
	});
};
Tomatic.weekday = function(short) {
	return {
		dl: 'Dilluns',
		dm: 'Dimarts',
		dx: 'Dimecres',
		dj: 'Dijous',
		dv: 'Divendres',
	}[short] || '??';
};
Tomatic.formatName = function(name) {
	function titleCase(str)
	{
		return str.replace(/\w\S*/g, function(txt){
			return txt.charAt(0).toUpperCase()
				+ txt.substr(1).toLowerCase();
		});
	}
	if (!name) { return "-";}
	return (Tomatic.grid().names||{})[name] || titleCase(name);
};
Tomatic.extension = function(name) {
	return Tomatic.formatName(name) + ": "
		+ ((Tomatic.grid().extensions||{})[name] || "???");
};
Tomatic.cell = function(day, houri, turni) {
	try {
		return Tomatic.grid().timetable[day][houri][turni];
	} catch(err) {
		return undefined;
	}
};
Tomatic.editCell = function(day,houri,turni,name) {
	// Direct edition, just for debug purposes
	//Tomatic.grid().timetable[day][houri][turni] = name;
	m.request({
		method: 'UPDATE',
		url: 'graella/'+([
			Tomatic.grid().week,day,houri,turni,name
			].join('/')),
		deserialize: jsyaml.load,
	})
	.then( function(data) {
		Tomatic.requestGrid(Tomatic.grid().week);
	}, function(error) {
		Tomatic.error("Problemes editant la graella: "+
			(error.error || "Inexperat"));
	});
};


Tomatic.weeks = m.prop([]);
Tomatic.currentWeek = m.prop(undefined);
Tomatic.requestWeeks = function() {
	m.request({
		method: 'GET',
		url: 'graella/list',
		deserialize: jsyaml.load,
	}).then(function(newWeeklist){
		let weeks = newWeeklist.weeks.sort().reverse();
		Tomatic.weeks(weeks);
		if (Tomatic.currentWeek()===undefined) {
			let expirationms = 1000*60*60*(24*4 + 18);
			let oldestWeek = new Date(new Date().getTime()-expirationms);
			let current = undefined;
			for (let i in weeks) {
				if (current!==undefined && new Date(weeks[i])<oldestWeek) {
					break;
				}
				current = weeks[i];
			}
			if (current!==undefined) {
				Tomatic.requestGrid(current);
			}
		}
	});
};

Tomatic.log = function(message) {
	console.log("log: ", message);
	SnackBar.show({
		containerSelector: '#snackbar',
		title: message,
	});
};

Tomatic.error = function(message) {
	console.log("error: ", message, ...arguments);
	SnackBar.show({
		containerSelector: '#snackbar',
		title: message,
		class: 'error',
	});
};

var Uploader = {
	controller: function(args) {
		var c = {};
		c.uploadFile = function(ev) {
			var formData = new FormData;
			formData.append("yaml", ev.target.files[0]);
			m.request({
				method: "POST",
				url: args.url,
				data: formData,
				serialize: function(value) {return value},
				deserialize: jsyaml.load,
			}).then(function(result) {
				Tomatic.init();
			}, function(error) {
				console.log("Upload error:", error);
				Tomatic.error("Upload error: " + error.error);
			});
		};
		return c;
	},
	view: function(c, args) {
		return m('.uploader',
			m('label', [
				m('input[type="file"]', {
					onchange: c.uploadFile.bind(c),
					accept: args.mimetype || "application/x-yaml",
				}),
				m.component(Button, {
					raised: true,
					label: args.label || 'Upload a file...',
				}),
			])
		);
	},
};

var Todo = function(message) {
	return m.component(Card, {
		content: [{
			primary: {
				title: 'TODO',
				subtitle: message,
			},
		}],
	});
};


var QueueWidget = {
	controller: function() {
		var c = {
			addtoqueue: function(ev) {
				Dialog.show({
					title: 'Obre una nova línia amb:',
					body: [
						m.component(PersonPicker, {
							id:'QueuePersonPicker',
							onpick: function(name) {
								Dialog.hide('QueuePersonPicker');
								Tomatic.addLine(name);
							}
						}),
					],
					footer: [
						m.component(Button, {
							label: "Cancel·la",
							events: {
								onclick: function() {
									Dialog.hide('QueuePersonPicker');
								},
							},
						}),
					],
				}, 'QueuePersonPicker');
			},
			resume: function(line, ev) {
				Tomatic.restoreLine(line);
			},
			pause: function(line, ev) {
				Tomatic.pauseLine(line);
			},
		};
		return c;
	},
	view: function(c) {
		return m('.queueeditor',
			Tomatic.queue().map(function(line) {
				return m('.queueitem.'+line.key, {
					'class': line.paused?'paused':'resumed',
					onclick: line.paused?
						c.resume.bind(c,line.key):
						c.pause.bind(c,line.key),
					},
					Tomatic.extension(line.key)
				);
			}),
			m('.queueitem.add', {
				onclick: c.addtoqueue.bind(c),
				},
				"+"
			)
		);
	}
};
var PersonPicker = {
	controller: function(args) {
		var c = {
			onpick: args.onpick,
			nobodyPickable: args.nobodyPickable,
			person: m.prop(undefined),
			picked: function(name, ev) {
				this.person(name);
				if (this.onpick) {
					this.onpick(name);
				}
			},
		};
		return c;
	},

	view: function(controller, args) {
		var pickCell = function(name) {
			return m('.extension', {
				class: name,
				onclick: controller.picked.bind(controller,name),
				},
				Tomatic.formatName(name)
			);
		};
		var extensions = Tomatic.grid().extensions || {};
		return m('.extensions', [
			Object.keys(extensions).sort().map(pickCell),
			args.nobodyPickable ? pickCell('ningu') : [],
		]);
	},
};

var WeekList = {
	controller: function(parentcontroller) {
		var controller = {
			model: this,
			parent: parentcontroller,
			setCurrent: function(week) {
				Tomatic.requestGrid(week);
			},
		};
		return controller;
	},
	view: function(c) {
		return m('.weeks',
			Tomatic.weeks().map(function(week){
				var current = Tomatic.currentWeek() === week ? '.current':'';
				return m('.week'+current, {
					onclick: function() {
						c.setCurrent(week);
					}
				}, "Setmana del "+week);
		}));
	}
};
const ButtonIcon = function(msvg) {
	return m.component(IconButton, {
		icon: {
			msvg: msvg
		},
		class: 'colored',
	});
};

const toolbarRow = function(title) {
	return [
		ButtonIcon(iconMenu),
		m('span.flex', title),
		ButtonIcon(iconMore)
	];
}


var TomaticApp = TomaticApp || {};

TomaticApp.controller = function(model, args) {
	args = args || {};
	var controller = {
		currentTab: m.prop('Graelles'),
	};
	return controller;
};

TomaticApp.view = function(c) {
	var grid = Tomatic.grid();
	return [
		m('style',
			Object.keys(grid.colors||{}).map(function(name) {
				let color = '#'+grid.colors[name];
				return (
					'.'+name+', .graella .'+name+' {\n' +
					'  background-color: '+color+';\n' +
					'  border-color: '+luminance(color,-0.3)+';\n' +
					'  border-width: 2pt;\n'+
					'}\n'+
					'.pe-dark-theme .'+name+', .pe-dark-theme .graella .'+name+' {\n' +
					'  background-color: '+luminance(color,-0.3)+';\n' +
					'  border-color: '+color+';\n' +
					'  border-width: 2pt;\n'+
					'}\n');
			})
		),
		m.component(HeaderPanel, {
			mode: 'waterfall-tall',
			//condenses: true, // condense: 
			//noReveal: true, // reveal: remove header when scroll down
			fixed: true,
			keepCondensedHeader: true,
			//animated: true,
			//disolve: true,
			headerHeight: 10,
			class: 'pe-header-panel--fit background-tomatic',
			header: {
				toolbar: {
					class: 'pe-toolbar--tabs.flex',
					topBar: toolbarRow('Tomàtic - Som Energia'),
					bottomBar: m('.tabArea.hasToolbar', [
						m.component(Tabs, {
							buttons: applicationPages,
							centered: true,
							activeSelected: true,
							getState: function(state) {
								c.currentTab(state.data.label);
							}
						})
					]),
				},
			},
			content: [
		c.currentTab()=='Centraleta' && [
			Todo([
				m('b','Sense cap efecte fins la centraleta.'),
				"Aqui podeu veure les línies que reben trucades, ",
				"pausar-les o afegir-ne de més. ",
				]),
			m('h2[style=text-align:center]', "Linies en cua"),
			m.component(QueueWidget, c),
		] || [],
		c.currentTab()=='Graelles' && [
			m('.layout.vertical', [
				m.component(WeekList, c),
				m('.layout.end-justified', [
					m.component(Uploader, {
						label: 'Puja Nova Graella',
						url: 'graella',
					}),
				]),
			]),
			m('.layout.center-center.wrap', Grid(grid)),
		] || [],
		(c.currentTab()=='Graelles' ) && [
			Extensions(grid.otherextensions),
			m('.layout.around-justified.wrap', [
				Forwardings(),
				Changelog(grid),
				Penalties(grid),
			]),
		] || [],
		c.currentTab() == 'Persones' && [
			Todo("Permetre modificar la configuració personal de cadascú: "+
				"Color, taula, extensió, indisponibilitats..."),
			Extensions(grid.extensions),
		] || [],
		c.currentTab() == 'Trucada' && [
			Todo(
				"Aquí es podrà veure informació de l'ERP sobre la trucada entrant"),
		] || [],
		m('#snackbar',m.component(SnackBar)),
		m.component(Dialog),
		]}
		),
	];
};

var Grid = function(grid) {
	var editCell = function(day, houri, turni) {
		var setPerson = function(name) {
			Tomatic.editCell(day, houri, turni, name)
			Dialog.hide('GridCellEditor');
		};
		var oldPerson = Tomatic.cell(day,houri,turni);
		Dialog.show({
			title: 'Edita posició de la graella',
			body: [
				Tomatic.weekday(day) +' a les '+
					Tomatic.grid().hours[houri] +
					', línia '+ (turni+1) +
					', la feia ',
				m('span.extension.'+oldPerson, Tomatic.formatName(oldPerson)),
				' qui ho ha de fer?',
				m.component(PersonPicker, {
					id:'GridCellEditor',
					onpick: setPerson,
					nobodyPickable: true,
				}),
			],
			footer: [
				m.component(Button, {
					label: "Cancel·la",
					events: {
						onclick: function() {
							Dialog.hide('GridCellEditor');
						},
					},
				}),
			],
		},'GridCellEditor');
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
			Tomatic.grid().extensions[name]?
				m('.tooltip', Tomatic.grid().extensions[name]):
				[],
			m.component(Ripple),
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
		m('h5', 'Penalitzacions'),
		m('ul.penalties', [
			grid.penalties?[]: m('li', 'La graella no te penalitzacions'),
			(grid.penalties || []).slice(-5).reverse().map(function(change) {
				return m('li',change);
			}),
			(grid.penalties || []).length > 5 ?  m('li', m.trust("&hellip;")) : [],
		]),
	]);
};


window.onload = function() {
	Tomatic.init();
	m.mount(document.getElementById("graella"), TomaticApp);
};

