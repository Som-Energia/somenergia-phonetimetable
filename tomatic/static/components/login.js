
module.exports = function() {

var m = require('mithril');
var jsyaml = require('js-yaml');
var getCookie = require('./utils').getCookie;

var Dialog = require('polythene-mithril-dialog').Dialog;
var Button = require('polythene-mithril-button').Button;
var List = require ('polythene-mithril-list').List;
var Ripple = require('polythene-mithril-ripple').Ripple;

var styleLogin = require('./callinfo_style.styl');
var Tomatic = require('./tomatic');
var Callinfo = require('./callinfo');

var Login = {};
var iden = "0";
var websock = null;
var port_ws = 0;
var tomaticCookie = "tomaticCookie"

function deyamlize(xhr) {
	return jsyaml.safeLoad(xhr.responseText);
}

var getServerSockInfo = function() {
    m.request({
        method: 'GET',
        url: '/api/socketInfo',
        extract: deyamlize,
    }).then(function(response){
        console.debug("Info GET Response: ",response);
        if (response.info.message !== "ok" ) {
            console.debug("Error get data: ", response.info.message);
			return;
		}
		port_ws = response.info.port_ws;
		connectWebSocket();
    }, function(error) {
        console.debug('Info GET apicall failed WebSock: ', error);
    });
}
getServerSockInfo();

Login.myName = function() {
    info = whoAreYou();
    aux = info.split(":");
    return aux[0];
}

Login.logout = function(){
    document.cookie = tomaticCookie + "=; expires = Thu, 01 Jan 1970 00:00:00 GMT;path=/";
	// sendIdentification();
}

function sendIdentification() {
    message = "IDEN:"+getMyExt()+":"+Login.myName()+":";
    websock.send(message);
}

var connectWebSocket = function() {
    var addr = 'ws://'+window.location.hostname+':'+port_ws+'/';
    websock = new WebSocket(addr);
    websock.onopen = sendIdentification;
    websock.onmessage = function (event) {
        var message = event.data.split(":");
        var type_of_message = message[0];
        if (type_of_message === "IDEN") {
            var iden = message[1];
            var ext = getMyExt();
            var info = {
                iden: iden,
                ext: (ext === "" ? -1 : ext),
            }
            Callinfo.refreshIden(info);
            Callinfo.getLogPerson();
        }
        else if (type_of_message === "PHONE") {
            var phone = message[1];
            var date = message[2]+":"+message[3]+":"+message[4];
            Callinfo.refreshPhone(phone, date);
            Callinfo.getLogPerson();
        }
        else if (type_of_message === "REFRESH") {
            Callinfo.getLogPerson();
        }
        else {
            console.debug("Message recieved from WebSockets and type not recognized.");
        }
    }
}

Date.prototype.addHours = function(h) {
   this.setTime(this.getTime() + (h*60*60*1000));
   return this;
}


var getMyExt = function() {
    var cookie_value = getCookie(tomaticCookie);
    if (cookie_value === ":") return "";
    return cookie_value.split(":")[1].toString();
}


var setCookieInfo = function(vnode){
    var name_button = vnode.target.innerText;
    var persons = Tomatic.persons().extensions;
    var found = false;
    for(id in persons){
        var name = Tomatic.formatName(id);
        if(name.toUpperCase() == name_button) {
            found = true;
            break;
        }
    }
    if(found){
        var value = id + ":" + Tomatic.persons().extensions[id] + ":" + Tomatic.persons().colors[id];
        var exp = new Date().addHours(3);
        var expires = "expires="+ exp.toUTCString();
        document.cookie = tomaticCookie + "=" + value + ";" + expires + ";path=/";
    }
    // sendIdentification();
}


var listOfPersons = function() {
    var aux = [];
    var persons = Tomatic.persons().extensions;

    for (id in persons){
        var name = Tomatic.formatName(id);
        var color = "#" + Tomatic.persons().colors[id];
		if (name == '-') {
            continue;
        }
        else if (name == '>>>CONTESTADOR<<<'){
            continue;
        }
        aux.push(m(Button, {
            id: id,
            className: 'btn-list',
            label: name,
            border: true,
            style: { backgroundColor: color },
            events: {
                onclick: function(id) {
                    setCookieInfo(id);
                    Dialog.hide({id:'whoAreYou'});
                },
            },
        }));
    }
    return m(List, { tiles:aux, className:'list-users' });
}


Login.askWhoAreYou = function() {
    Dialog.show(function() { return {
        className: 'dialog-login',
        title: 'Qui ets?',
        backdrop: true,
        body: [
            listOfPersons()
        ],
        footerButtons: [
            m(Button, {
                label: "Cancel·la",
                events: {
                    onclick: function() {
                        Dialog.hide({id:'whoAreYou'});
                    },
                },
            }),
        ],
        didHide: function() {m.redraw();}
    };},{id:'whoAreYou'});
}

var whoAreYou = function() {
    var cookie = getCookie(tomaticCookie);
    return (cookie === "" ? ":" : cookie);
}

var exitIcon = function(){
    return m(".icon-exit", [
        m("i.fas.fa-times-circle"),
    ]);
}

Login.identification = function() {
    var info = whoAreYou();
    var nom = "IDENTIFICAR";
    var color = 'rgba(255, 255, 255, 0.7)';

    if (info !== ":") {
        var aux = info.split(":");
        var id = aux[0];
        nom = Tomatic.formatName(id);
        color = "#" + aux[2];
        if(iden !== nom || websock === null){
            iden = nom;
        }
    }

    return m('.login-buttons', [
        m(Button, {
            className: 'btn-iden',
            label: nom,
            border: true,
            events: {
                onclick: function() {
                    Login.askWhoAreYou();
                },
            },
            style: { backgroundColor: color },
        }, m(Ripple)),
        m(Button, {
            className: 'btn-disconnect',
            label: exitIcon(),
            events: {
                onclick: Login.logout,
            },
        }, m(Ripple)),
    ]);
}



return Login;

}();

// vim: noet ts=4 sw=4
