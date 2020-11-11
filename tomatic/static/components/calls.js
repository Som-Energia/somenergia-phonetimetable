module.exports = function() {

var m = require('mithril');
var deyamlize = require('./utils').deyamlize;

var Ripple = require('polythene-mithril-ripple').Ripple;
var Dialog = require('polythene-mithril-dialog').Dialog;
var Button = require('polythene-mithril-button').Button;
var Textfield = require('polythene-mithril-textfield').TextField;
var Card = require('polythene-mithril-card').Card;
var ListTile = require('polythene-mithril-list-tile').ListTile;
var List = require ('polythene-mithril-list').List;
var Spinner = require('polythene-mithril-material-design-spinner').MaterialDesignSpinner;
var Checkbox = require('polythene-mithril-checkbox').Checkbox;
var RadioButton = require('polythene-mithril-radio-button').RadioButton
var RadioGroup = require('polythene-mithril-radio-group').RadioGroup;

var Calls = {};
var history = [];

Calls.getLog = function(phone) {
  history=[];
  history.push("lookingfor");
  m.request({
    method: 'GET',
    url: '/api/log/'+phone,
    extract: deyamlize,
  }).then(function(response){
    console.debug("Info GET Response: ", response);
    if (response.info.message !== "ok" ) {
      console.debug("Error al obtenir els motius: ", response.info.message)
      history = [];
    }
    else {
      history = response.info.info;
    }
  }, function(error) {
    console.debug('Info GET apicall failed: ', error);
    history = [];
  });
};

var llistaLog = function() {
  var aux = [];
  for(var i = history.length-1; i>=0; i--) {
    var missatge = history[i][1] + " (" + history[i][0] + "): " + history[i][3];
    aux.push(m(ListTile, {
      className: "registres",
      compact: true,
      title: missatge,
    }));
  }
  if (history.length === 0) {
    aux[0] = m(ListTile, {
      className: "registres",
      compact: true,
      title: "No hi ha cap registre",
    });
  }
  return m(".logs", m(List, { compact: true, tiles: aux }));
}

Calls.logCalls = function() {
  return m(Card, {
    className: 'card-log',
    content: [
      { primary: { title: m(".title", 'Històric:') } },
      { text: {
        content: ( history[0] === "lookingfor" ?
          m('center', m(Spinner, { show: "true" } )) : llistaLog())
      }},
    ]
  });
}

return Calls;
}();

// vim: noet ts=4 sw=4
