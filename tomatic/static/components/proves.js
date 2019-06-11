module.exports = function() {

var m = require('mithril');
var jsyaml = require('js-yaml');

var Ripple = require('polythene-mithril-ripple').Ripple;
var List = require ('polythene-mithril-list').List;
var ListTile = require('polythene-mithril-list-tile').ListTile;
var Card = require('polythene-mithril-card').Card;
var Button = require('polythene-mithril-button').Button;
var Tabs = require('polythene-mithril-tabs').Tabs;

var styleProves = require('./proves_style.styl');

var Proves = {};

Proves.main_partner = 0;


var infoPartner = function(info){
    // var lang = info.lang;
    var url = "https://secure.helpscout.net/search/?query=" + info.email;
    var dni = (info.dni.slice(0,2) === 'ES' ? info.dni.slice(2) : info.dni)
    return m(".partner-info",
        [
            m(".partner-info-item", [
                m("", m(".label-right",info.id_soci)),
                m("", m(".label",info.name))
            ]),
            m(".partner-info-item", dni),
            m(".partner-info-item", info.state),
            m(".partner-info-item", m("a", {"href":url, target:"_blank"}, info.email)),
            m(".partner-info-item", m(".label","Ha obert OV? "), (info.ov ? "Sí" : "No")),
        ]
    );
}


var contractCard = function(info) {
    var from_til = (info.start_date !== false ? info.start_date : "No especificat");
    var aux = info.end_date;
    var num = info.number
    var s_num = num+"";
    var last_invoiced = (info.last_invoiced != "" ? info.last_invoiced : "No especificada")
    while (s_num.length < 7) s_num = "0" + s_num;
    if (aux == "" && from_til !== "No especificat") {
        from_til += " ⇨ Actualitat"
    }
    else if (from_til !== "No especificat") {
        from_til += (" ⇨ " + aux);
    }
    return m(".contract-info", [
            m(".contract-info-box", [
                    m(".contract-info-item", [
                        m("", m(".label-right", from_til)),
                        m("", m(".label","Número: "), s_num),
                    ]),
                    m(".contract-info-item", m('.label', "CUPS: "), info.cups),
                    m(".contract-info-item", m('.label', "Potència: "), info.power),
                    m(".contract-info-item", m('.label', "Tarifa: "), info.fare),
                    m(".contract-info-item", m('.label', "Data última lectura facturada: "), last_invoiced),
                    m(".contract-info-item", (info.has_open_r1s ? m(".label-alert","Casos ATR R1 oberts.") : "")),
                    m(".contract-info-item", (info.has_open_bs ? m(".label-alert","Cas ATR B1 obert.") : "")),
                    m(".contract-info-item", m('.label', "Facturació suspesa: "), (info.suspended_invoicing ? "Sí" : "No")),
                    m(".contract-info-item", [
                        m(".label-right", [
                            (info.is_titular ? "T " : ""),
                            (info.is_partner ? "S " : ""),
                            (info.is_payer ? "P " : ""),
                            (info.is_notifier ? "N " : ""),
                        ]),
                        m("", m('.label', "Estat pendent: "), info.pending_state),
                    ]),
                ]
            )
        ]
    );
}


var contractsField = function(info){
    var contract = 0;
    var aux = ["ini"];
    try{
      var numOfContracts = info.length;
    }
    catch(error) {
        aux[0] = m("center","No hi ha contractes.");
    }
    if(aux[0]==="ini"){
        for (contract; contract < numOfContracts; contract++) {
            aux[contract] = contractCard(info[contract]);
        }
    }
    return m(".contract-field",
        [
            m(List, {
                tiles: [ aux ],
            })
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
    }

    return m(List, {
      tiles: [ aux[Proves.main_partner] ],
    });
}


var specificPartnerCard = function(partner, button) {
    return m(".partner-card", [
        m(Tabs, {
            class: 'partner-tabs',
            selected: "true",
            autofit: "true",
            all: {
                activeSelected: "true",
                ink: "true",
            },
            tabs: button,
            onChange: ({ index }) => {
                Proves.main_partner = index
            }
        }),
        m(Card, {
            class: 'card-info',
            content: [
                { text: {
                    content: m("", [
                        infoPartner(partner),
                        contractsField(partner.contracts)
                    ])
                }},
            ]
        })
    ]);
}


Proves.allInfo = function(info, phone) {
    return m(".main-info-card", listOfPartners(info.partners, buttons(info.partners)));
}

return Proves;

}();