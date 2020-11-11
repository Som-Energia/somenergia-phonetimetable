// Tomatic application model component
module.exports = function() {

var Snackbar = require('polythene-mithril-snackbar').Snackbar;

var jsyaml = require('js-yaml');
var m = require('mithril');
m.prop = require('mithril/stream');

function deyamlize(xhr) {
	return jsyaml.safeLoad(xhr.responseText);
}

var Tomatic = {
};

Tomatic.queue = m.prop([]);
Tomatic.persons = m.prop({});
Tomatic.init = function() {
	this.requestWeeks();
	this.requestQueue();
	this.requestPersons();
};
Tomatic.requestPersons = function() {
	return m.request({
		method: 'GET',
		url: '/api/persons',
		extract: deyamlize,
	}).then(function(response){
		if (response.persons!==undefined) {
			Tomatic.persons(response.persons);
		}
	});
};


// Line management

Tomatic.requestQueue = function(suffix) {
	m.request({
		method: 'GET',
		url: '/api/queue'+(suffix||''),
		extract: deyamlize,
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
Tomatic.weekdays = {
	dl: 'Dilluns',
	dm: 'Dimarts',
	dx: 'Dimecres',
	dj: 'Dijous',
	dv: 'Divendres',
};


Tomatic.requestGrid = function(week) {
	m.request({
		method: 'GET',
		url: '/api/graella-'+week+'.yaml',
		extract: deyamlize,
	}).then(function(data) {
		data.days = data.days || 'dl dm dx dj dv'.split(' ');
		delete data.colors;
		delete data.names;
		delete data.extensions;
		delete data.tables; // TODO: This one was never added
		Tomatic.currentWeek(week);
		Tomatic.grid(data);
	});
};
Tomatic.weekday = function(short, alternative) {
	return Tomatic.weekdays[short] || alternative || '??';
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
	return (Tomatic.persons().names||{})[name] || titleCase(name);
};
Tomatic.extension = function(name) {
	return Tomatic.formatName(name) + ": "
		+ ((Tomatic.persons().extensions||{})[name] || "???");
};
Tomatic.table = function(name) {
	var tables = Tomatic.persons().tables;
	if (!tables) { Tomatic.persons().tables={}; } // TODO: Move that anywhere else
	var table = Tomatic.persons().tables[name];
	if (table == undefined) { return -1; }
	return table;
};
Tomatic.peopleInTable = function(table) {
	var tables = Tomatic.persons().tables || {};
	var result = Object.keys(tables).filter(function(k) {
		return Tomatic.table(k)===table;
		});
	return result;
};
Tomatic.cell = function(day, houri, turni) {
	try {
		return Tomatic.grid().timetable[day][houri][turni];
	} catch(err) {
		return undefined;
	}
};
Tomatic.editCell = function(day,houri,turni,name,myname) {
	// Direct edition, just for debug purposes
	//Tomatic.grid().timetable[day][houri][turni] = name;
	m.request({
		method: 'UPDATE',
		url: '/api/graella/'+([
			Tomatic.grid().week,day,houri,turni,name
			].join('/')),
		body: myname,
		extract: deyamlize,
	})
	.then( function(data) {
		Tomatic.requestGrid(Tomatic.grid().week);
	}, function(error) {
		Tomatic.error("Problemes editant la graella: "+
			(error.error || "Inexperat"));
	});
};
Tomatic.setPersonData = function (name, data) {
	if (name===undefined) {
		name = data.name;
	}
	var postdata = {};

	for (var key in data) {
		var value = data[key];
		switch (key) {
		case 'formatName':
			delete Tomatic.persons().names[name];
			var formatName = Tomatic.formatName(name);
			if (formatName!==value) {
				postdata.name = value;
			}
			break;
		case 'extension':
			postdata.extension = value;
			break;
		case 'table':
			postdata.table = parseInt(value,10);
			break;
		case 'color':
			postdata.color = value;
			break;
		case 'email':
			postdata.email = value;
			break;
		}
	}
	console.log("posting",postdata);
	m.request({
		method: 'POST',
		url: '/api/person/'+name,
		data: postdata,
		extract: deyamlize,
	})
	.then( function(data) {
		Tomatic.requestPersons();
	}, function(error) {
		console.log(error);
		Tomatic.error("Problemes editant la persona: "+
			(error.error || "Inexperat"));
	});
};


Tomatic.weeks = m.prop([]);
Tomatic.currentWeek = m.prop(undefined);
Tomatic.requestWeeks = function() {
	m.request({
		method: 'GET',
		url: '/api/graella/list',
		extract: deyamlize,
	}).then(function(newWeeklist){
		var weeks = newWeeklist.weeks.sort().reverse();
		Tomatic.weeks(weeks);
		if (Tomatic.currentWeek()===undefined) {
			var expirationms = 1000*60*60*(24*4 + 18);
			var oldestWeek = new Date(new Date().getTime()-expirationms);
			var current = undefined;
			for (var i in weeks) {
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
	Snackbar.show({
		containerSelector: '#snackbar',
		title: message,
	});
};

Tomatic.error = function(message) {
	console.log("error: ", message);
	Snackbar.show({
		containerSelector: '#snackbar',
		title: message,
		className: 'error',
		timeout: 10,
	});
};

Tomatic.sendBusyData = function(name, data) {
	console.log("retrieving", name,  '/api/busy/'+name);
	m.request({
		method: 'POST',
		url: '/api/busy/'+name,
		data: data,
		extract: deyamlize,
	}).then(function(response){
		console.debug("Busy POST Response: ",response);
		if (response.result==='ok') { return; }
		console.debug('apicall failed:', response.error);
		Tomatic.error("Problemes desant les indisponibilitats: "+
			(response.message));
	}, function(error) {
		console.debug('Busy POST apicall failed:', error);
		Tomatic.error("Problemes desant les indisponibilitats: "+
			(error || "Inexperat"));
	});
};

Tomatic.retrieveBusyData = function(name, callback) {
	console.log("retrieving", name,  '/api/busy/'+name);
	m.request({
		method: 'GET',
		url: '/api/busy/'+name,
		extract: deyamlize,
	}).then(function(response){
		console.debug("Busy GET Response: ",response);
		callback(response);
		if (response.errors && response.errors.lenght ) {
			Tomatic.error("Problemes carregant a les indisponibilitats:\n"+
				response.errors.join("\n"));
		}
	}, function(error) {
		console.debug('Busy GET apicall failed:', error);
		Tomatic.error("Problemes carregant a les indisponibilitats: "+
			(error || "Inexperat"));
	});
};
Tomatic.retrieveBusyDataFake = function(name, callback) {
	console.log("simulating retrieval", name);
	setTimeout(function () {
		callback( {
			'oneshot': [
				{
					'date': '2013-06-23',
					'turns': '0011',
					'optional': true,
					'reason': 'motivo 0',
				},
				{
					'date': '2013-12-23',
					'turns': '0110',
					'optional': false,
					'reason': 'motivo 1',
				},
				{
					'date': '2017-02-23',
					'turns': '1100',
					'optional': true,
					'reason': 'motivo 2',
				},
				{
					'date': '2019-12-25',
					'turns': '1111',
					'optional': false,
					'reason': 'me quedo en casa rascandome los gatos',
				},
			],
			'weekly': [
				{
					'weekday': 'dm',
					'turns': '1111',
					'optional': false,
					'reason': 'motivo 3',
				},
				{
					'weekday': '',
					'turns': '0011',
					'optional': false,
					'reason': 'me quedo en casa rascandome los gatos',
				},
			],
		});
	},1000);
};


return Tomatic;
}();

// vim: noet ts=4 sw=4
