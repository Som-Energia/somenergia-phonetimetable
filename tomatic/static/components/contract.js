module.exports = function() {

var m = require('mithril');
var jsyaml = require('js-yaml');

var Ripple = require('polythene-mithril-ripple').Ripple;
var Card = require('polythene-mithril-card').Card;
var Button = require('polythene-mithril-button').Button;
var Tabs = require('polythene-mithril-tabs').Tabs;

var Questionnaire = require('./questionnaire');

var ContractInfo = {};

ContractInfo.main_contract = 0;

var clipboardIcon = function(){
    return m(".icon-clipboard",
    [
        m("i.far.fa-clipboard"),
    ]);
}

var contractCard = function(info, partner_id) {
  var from_til = (info.start_date !== false ?
    info.start_date : "No especificat"
  );
  var aux = info.end_date;
  var num = info.number
  var s_num = num+"";
  var last_invoiced = (info.last_invoiced != "" ?
    info.last_invoiced : "No especificada"
  );
  while (s_num.length < 7) s_num = "0" + s_num;
  if (aux == "" && from_til !== "No especificat") {
    from_til += " ⇨ Actualitat"
  }
  else if (from_til !== "No especificat") {
    from_til += (" ⇨ " + aux);
  }
  return m(".contract-info-box", [
    m(".contract-info-item", [
      m("", m(".label-right", from_til)),
      m("", m(".label","Número: "), s_num),
    ]),
    m(
      ".contract-info-item",
      m('.label', "Nom del titular: "),
      info.titular_name
    ),
    m(
      ".contract-info-item",
      m('.label', "CUPS: "),
      info.cups
    ),
    m(
      ".contract-info-item",
      m('.label', "Adreça CUPS: "),
      info.cups_adress
    ),
    m(".contract-info-item", [
      m("", m(".label-right", (
        info.generation ? m(".label-generation","Té Generation.") : ""
      ))),
      m("", m('.label', "Potència: "), info.power),
    ]),
    m(".contract-info-item", [
      m("", m(".label-right", (
        info.energetica ? m(".label-energetica","És Energetica.") : ""
      ))),
      m("", m('.label', "Tarifa: "), info.fare),
    ]),
    m(
      ".contract-info-item",
      (info.suspended_invoicing ? m(".label-alert","Facturació suspesa.") : "")
    ),
    m(
      ".contract-info-item",
      m('.label', "Lot facturació: "),
      info.lot_facturacio
    ),
    m(
      ".contract-info-item",
      m('.label', "Data última lectura facturada: "),
      last_invoiced
    ),
    m(
      ".contract-info-item",
      (info.open_cases.length > 0 ?
        m(".label-alert", ["Casos ATR oberts: ", info.open_cases])
        : ""
      )
    ),
    m(".contract-info-item", [
      m(".label-right", [
        m(Button, {
          label: clipboardIcon(),
          border: 'true',
          events: {
            onclick: function() {
              Questionnaire.motiu(
                { 'cups': info.cups, 'number': s_num },
                partner_id
              );
            },
          },
        }, m(Ripple))
      ]),
      m('.label', "IBAN: "),
      info.iban
    ]),
    m(
      ".contract-info-item",
      m('.label', "Estat pendent: "),
      (info.pending_state != "" ? info.pending_state : "No especificat")
    ),
    m(".contract-info-item", [
      m(".label-right", [
        (info.is_titular ? "T " : ""),
        (info.is_partner ? "S " : ""),
        (info.is_payer ? "P " : ""),
        (info.is_notifier ? "N " : ""),
      ]),
      m(
        "",
        (info.no_estimable ?
          m('.label', "No estimable.")
          : m('.label', "Estimable.")
        )
      ),
    ]),
    meterReadings(info.lectures_comptadors),
    lastInvoices(info.invoices),
  ]);
}

var meterReadings = function(readings) {
  if (readings.length == 0) {
    return m(".contract-info-item", "No hi ha informació de comptadors.")
  }
  meter_readings = [];
  meter_readings.push(
    m("tr", [
      m("th", "Comptador"),
      m("th", "Data"),
      m("th", "Lectura"),
      m("th", "Origen"),
      m("th", "Període")
    ])
  );
  for (reading_index in readings) {
    reading = readings[reading_index];
    meter_readings.push(
      m("tr", [
        m("td", reading.comptador),
        m("td", reading.data),
        m("td", reading.lectura),
        m("td", reading.origen),
        m("td", reading.periode)
      ])
    )
  }
  return m(".meter-readings", m("table", meter_readings));
}

var lastInvoices = function(invoices) {
  last_invoices = [];
  for (invoice_index in invoices) {
    invoice = invoices[invoice_index];
    last_invoices.push(
      m(".factura-info-item", [
        m("div", [
          m(".label-right", invoice.initial_date, " ⇨ ", invoice.final_date),
          m("", m(".label", "Factura: "), invoice.number),
        ]),
        m("div", [m(".label", "Empresa: "), invoice.payer]),
        m("table", [
          m("tr", [
            m("th", "Total"),
            m("th", "Energia"),
            m("th", "Dies"),
            m("th", "Data"),
            m("th", "Venciment"),
            m("th", "Estat")
          ]),
          m("tr", [
            m("td", invoice.amount),
            m("td", invoice.energy_invoiced),
            m("td", invoice.days_invoiced),
            m("td", invoice.invoice_date),
            m("td", invoice.due_date),
            m("td", invoice.state),
          ])
        ])
      ])
    )
  }
  return m(".factures", m(".factures-info", last_invoices));
}

var buttons = function(info) {
    var contract = 0;
    var numOfContracts = info.length;
    var aux = [];
    for (contract; contract < numOfContracts; contract++) {
        aux[contract] = {label: info[contract].number};
    }

    return aux;
}

var listOfContracts = function(contracts, button, partner_id) {
  var contract = 0;
  var numOfContracts = contracts.length;
  var aux = [];

  for (contract; contract < numOfContracts; contract++) {
    aux[contract] = specificContractCard(
      contracts[contract],
      button,
      partner_id
    );
  }
  return aux[ContractInfo.main_contract];
}

var specificContractCard = function(contract, button, partner_id) {
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
          ContractInfo.main_contract = ev.index
        }
      }),
    ]),
    m(Card, {
      class: 'card-info',
      content: [
        { text: {
          content: m("", [
            contractCard(contract, partner_id),
          ])
        }},
      ]
    }),
  ]);
}

ContractInfo.listOfContracts = function(info, main_partner) {
  if (info.partners[main_partner].contracts == undefined) {
    return m(".contracts", [m(".no-info", "No hi ha contractes.")]);
  }
  return m(
    ".contracts",
    listOfContracts(
      info.partners[main_partner].contracts,
      buttons(info.partners[main_partner].contracts),
      info.partners[main_partner].id_soci
    )
  );
}


return ContractInfo;

}();
