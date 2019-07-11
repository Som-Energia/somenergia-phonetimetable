
module.exports = function() {

var m = require('mithril');
var jsyaml = require('js-yaml');

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
var ip = "";
var port_ws = 0;


var getServerSockInfo = function() {
    m.request({
        method: 'GET',
        url: '/api/socketInfo',
        deserialize: jsyaml.load,
    }).then(function(response){
        console.debug("Info GET Response: ",response);
        if (response.info.message !== "ok" ) {
            console.debug("Error get data: ", response.info.message);
			return;
		}
		ip = response.info.ip;
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
    document.cookie = "; expires = Thu, 01 Jan 1970 00:00:00 GMT;path=/";
	sendIdentification();
}

function sendIdentification() {
	websock.send(getMyExt());
}

var connectWebSocket = function() {
    var addr = 'ws://'+ip+':'+port_ws+'/';
    websock = new WebSocket(addr);
    websock.onopen = sendIdentification;
    websock.onmessage = function (event) {
        var content = event.data;
        Callinfo.refreshInfo(content);
    }
}

Date.prototype.addHours = function(h) {
   this.setTime(this.getTime() + (h*60*60*1000));
   return this;
}



var getMyExt = function() {
    var cookie = document.cookie;
    return (cookie !== "" ? cookie.split(":")[1].toString() : cookie);
}


var setCookieInfo = function(vnode){
    var aux = vnode.attributes;
    var name_button = aux["0"].ownerElement.innerText;
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
        document.cookie = value + ";" + expires + ";path=/";
    }
    sendIdentification();
}


var listOfPersons = function() {
    var aux = [];
    var persons = Tomatic.persons().extensions;

    for (id in persons){
        var name = Tomatic.formatName(id);
        var color = "#" + Tomatic.persons().colors[id];
		// DGG: Turn this into two continue's
        if (name !== '-' && name !== '>>>CONTESTADOR<<<'){
            aux.push(m(Button, {
                className: 'btn-list',
                label: name,
                border: true,
                style: { backgroundColor: color },
                events: {
                    onclick: function() {
                        setCookieInfo(this);
                        Dialog.hide({id:'whoAreYou'});
                    },
                },
            }));
        }
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
    var cookie = document.cookie;
    return (cookie === "" ? ":" : cookie);
}

var exitIcon = function(){
    return m(".icon-exit", [
        m("i.fas fa-times-circle"),
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
