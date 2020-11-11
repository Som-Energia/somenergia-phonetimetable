module.exports = function() {

var m = require('mithril');

var Ripple = require('polythene-mithril-ripple').Ripple;
var Card = require('polythene-mithril-card').Card;
var Button = require('polythene-mithril-button').Button;
var Tabs = require('polythene-mithril-tabs').Tabs;

var ContractInfo = require('./contract');

var PartnerInfo = {};
PartnerInfo.main_partner = 0;
PartnerInfo.info = {};

var infoPartner = function(info){
  var aux = info.email.split(",");
  var emails = [];
  var url = "https://secure.helpscout.net/search/?query=";
  for(var i=0; i<aux.length; i++){
    emails.push(
      m(".partner-info-item",
        m("a", {"href":url+aux[i], target:"_blank"}, aux[i])
      )
    );
  }
  var dni = (info.dni.slice(0,2) === 'ES' ? info.dni.slice(2) : info.dni)
  return m(".partner-info",
    [
      m(".partner-info-item", [
        m("", m(".label-right",info.id_soci)),
        m("", m(".label",info.name))
      ]),
      m(".partner-info-item", dni),
      m(".partner-info-item", [info.city, ", ", info.state]),
      m(".partner-info-item", m("", emails)),
      m(".partner-info-item", (info.energetica ?
        m(".label-energetica","Soci d'Energetica.") : "")
      ),
      m(".partner-info-item", [
        m("", m(".label-right",info.lang)),
        m("", m(".label","Ha obert OV? "), (info.ov ? "Sí" : "No"))
      ]),
    ]
  );
}


var buttons = function(info) {
  var partner = 0;
  var numOfPartners = info.length;
  var aux = [];
  for (partner; partner < numOfPartners; partner++) {
    var name = info[partner].name;
    var aux2 = name.split(',');
    if (!aux2[1]){
      aux2 = name.split(' ');
      aux2[1] = aux2[0];
    }
    aux[partner] = {label: aux2[1]};
  }
  return aux;
}

var listOfPartners = function(partners, button) {
  var partner = 0;
  var numOfPartners = partners.length;
  var aux = [];
  for (partner; partner < numOfPartners; partner++) {
    aux[partner] = specificPartnerCard(partners[partner], button);
    PartnerInfo.info[partner] = partners[partner];

  }
  return aux[PartnerInfo.main_partner];
}

var specificPartnerCard = function(partner, button) {
  return m(".partner-card", [
    m(".partner-tabs", [
      m(Tabs, {
        selected: "true",
        scrollable: "true",
        all: {
          activeSelected: "true",
          ink: "true",
        },
        tabs: button,
        onChange: function(ev) {
          PartnerInfo.main_partner = ev.index
          ContractInfo.main_contract = 0
        }
      }),
    ]),
    m(Card, {
      className: 'card-info',
      content: [
        { text: {
          content: m("", [
            infoPartner(partner),
          ])
        }},
      ]
    })
  ]);
}


PartnerInfo.allInfo = function(info) {
  return m(
    ".main-info-card", [
      listOfPartners(info.partners, buttons(info.partners)),
    ]
  );
}

return PartnerInfo;

}();
