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
var Checkbox = require('polythene-mithril-checkbox').Checkbox;

var PartnerInfo = require('./partnerinfo');

var Questionnaire = {};

Questionnaire.call = {
    'phone': "",
    'date': "",
    'reason': "",
    'extra': "",
    'log_call_reasons': [],
    "iden": "",
    "ext": "",
};

var extras_dict = {}
var reason_filter = "";
var call_reasons = {
    'general': [],
    'extras': []
}
var desar = "Desa";


function getExtras(extras) {
  var reasons = [];
  for (extra in extras) {
    reasons.push(extras_dict[extras[extra]]);
  }
  return reasons;
}

var getClaims = function() {
  m.request({
      method: 'GET',
      url: '/api/getClaims',
      extract: deyamlize,
  }).then(function(response){
      console.debug("Info GET Response: ",response);
      if (response.info.message !== "ok" ) {
          console.debug("Error al obtenir les reclamacions: ", response.info.message)
      }
      else{
        call_reasons.general = response.info.claims;
        extras_dict = response.info.dict;
        call_reasons.extras = Object.keys(response.info.dict);
      }
  }, function(error) {
      console.debug('Info GET apicall failed: ', error);
  });
};
getClaims();
Questionnaire.getClaims = getClaims();

var postClaim = function(info) {
  m.request({
    method: 'POST',
    url: '/api/atrCase',
    extract: deyamlize,
    body: info
  }).then(function(response){
    console.debug("Info GET Response: ",response);
    if (response.info.message !== "ok" ) {
      console.debug("Error al fer el post del cas atr: ", response.info.message)
    }
    else{
      console.debug("ATC case saved")
      desar='Desa';
    }
  }, function(error) {
    console.debug('Info GET apicall failed: ', error);
  });
};


var postReclama = function(claim) {
  m.request({
    method: 'POST',
    url: '/api/claimReasons',
    data: claim,
    extract: deyamlize,
  }).then(function(response){
    console.debug("Info POST Response: ",response);
    if (response.info.message !== "ok" ) {
      console.debug("Error al desar motius telefon: ", response.info.message)
    }
  }, function(error) {
    console.debug('Info POST apicall failed: ', error);
  });
}


var postInfo = function(phone, info) {
  m.request({
    method: 'POST',
    url: '/api/infoReasons',
    data: info,
    extract: deyamlize,
  }).then(function(response){
    console.debug("Info POST Response: ",response);
    if (response.info.message !== "ok" ) {
      console.debug("Error al desar motius telefon: ", response.info.message)
    }
    else if (Questionnaire.call['phone'] === phone) {
      desar='Desa';
      Questionnaire.call.extra="";
      reason_filter="";
      Questionnaire.call.proc=false;
      Questionnaire.call.improc=false;
    }
  }, function(error) {
    console.debug('Info POST apicall failed: ', error);
  });
}

var updateCall = function(date, partner_number, contract_number) {
    var info = {
        'data': Questionnaire.call.date,
        'telefon': Questionnaire.call.phone,
        'partner': partner_number,
        'contracte': contract_number,
        'motius': Questionnaire.call.reason,
    }
    m.request({
        method: 'POST',
        url: '/api/' + 'updatelog/'+ Questionnaire.call.ext,
        body: info,
        extract: deyamlize,
    }).then(function(response){
        console.debug("Info POST Response: ",response);
        if (response.info.message !== "ok") {
            console.debug("Error al fer log dels motius: ", response.info.message)
        }
        Questionnaire.call.date = "";
    }, function(error) {
        console.debug('Info POST apicall failed: ', error);
    });
}

var saveLogCalls = function(
  phone, person, reclamacio, contract_info, partner_number) {
  desar = 'Desant';
  contract_number = contract_info.number;
  contract_cups = contract_info.cups;
  updateCall(Questionnaire.call["date"], partner_number, contract_number);
  info = {
    "date": Questionnaire.call.date,
    "phone": Questionnaire.call.phone,
    "person": person,
    "reason": Questionnaire.call.reason,
    "extra": Questionnaire.call.extra,
  }
  if (reclamacio == "") {
      //postInfo(phone, info);
  }
  else {
    claim = {
      "date": Questionnaire.call.date,
      "person": person,
      "reason": Questionnaire.call.reason,
      "partner": partner_number,
      "contract": contract_number,
      "procedente": (reclamacio.proc ? "x" : ""),
      "improcedente": (reclamacio.improc ? "x" : ""),
      "solved": (reclamacio.solved ? "x" : ""),
      "user": (reclamacio.tag ? reclamacio.tag : "INFO"),
      "cups": contract_cups,
      "observations": Questionnaire.call.extra,
    }
    //postInfo(phone, info);
    //postReclama(claim);
    postClaim(claim);
  }
}

var llistaMotius = function() {
  function conte(value) {
    var contains = value.toLowerCase().includes(reason_filter.toLowerCase());
    return contains;
  }
  var list_reasons = call_reasons.general;
  if (reason_filter !== "") {
    var filtered_regular = list_reasons.filter(conte);
    var filtered_extras = call_reasons.extras.filter(conte);
    var extras = getExtras(filtered_extras);
    var filtered = filtered_regular.concat(extras);
  }
  else {
    list_reasons = call_reasons.general;
    var filtered = list_reasons;
  }
  var disabled = (desar === "Desant" || Questionnaire.call.date === "" );
  return m(".motius", m(List, {
    compact: true,
    indentedBorder: true,
    tiles: filtered.map(function(reason) {
      return m(ListTile, {
        className: (Questionnaire.call.reason === reason ?
          "llista-motius-selected" :
          "llista-motius-unselected"),
        compact: true,
        selectable: true,
        ink: 'true',
        ripple: {
          opacityDecayVelocity: '0.5',
        },
        title: reason,
        selected: Questionnaire.call.reason == reason,
        events: {
            onclick: function(ev) {
                Questionnaire.call['reason'] = reason
            }
        },
        disabled: disabled,
         bordered: true,
       });
    }),
  }));
}

Questionnaire.motiu = function(main_contract, partner_id) {

  var enviar = function(reclamacio="") {
    saveLogCalls(
      Questionnaire.call.phone,
      Questionnaire.call.iden,
      reclamacio,
      main_contract,
      partner_id
    );
    Questionnaire.call.reason="";
  }

  var getTag = function(reason) {
    var matches = reason.match(/\[(.*?)\]/);
    if (matches) {
      return matches[1].trim();
    }
    return "";
  }

  var esReclamacio = function(type) {
    info = "INFO";
    return (type != info);
  }

  var seleccionaUsuari = function(reclamacio, tag) {
    var section = tag;
    var options = [
      "RECLAMA",
      "FACTURA",
      "COBRAMENTS",
      "ATR A - COMER",
      "ATR B - COMER",
      "ATR C - COMER",
      "ATR M - COMER"
    ]
    return m("", [
      m("p", "Secció: " ),
      m("select",
        {
          id: "select-user",
          class: ".select-user",
          disabled: section !== "ASSIGNAR USUARI",
          default: section,
          onchange: function() {
            reclamacio.tag = document.getElementById("select-user").value;
          },
        },
        [
          m("option", {
            "value": options[0],
            "selected": section === options[0]
          }, options[0]),
          m("option", {
            "value": options[1],
            "selected": section === options[1]
          }, options[1]),
          m("option", {
            "value": options[2],
            "selected": section === options[2]
          }, options[2]),
          m("option", {
            "value": options[3],
            "selected": section === options[3]
          }, options[3]),
          m("option", {
            "value": options[4],
            "selected": section === options[4]
          }, options[4]),
          m("option", {
            "value": options[5],
            "selected": section === options[5]
          }, options[5]),
          m("option", {
            "value": options[6],
            "selected": section === options[6]
          }, options[6]),
          m("option", {
            "value": section,
            "selected": !options.includes(section)
          }, section)
        ]
      )
    ]);
  }

  var tipusATR = function(reclamacio) {
    return m("", [
      m("p", "Tipus: "),
      m(Checkbox, {
        className: "checkbox",
        name: 'proc',
        checked: reclamacio.proc,
        label: "Procedente",
        onChange: function() {
          reclamacio.proc = !Questionnaire.call.proc;
          reclamacio.improc = false
        },
      }),
      m("br"),
      m(Checkbox, {
        className: "checkbox",
        name: 'improc',
        checked: reclamacio.improc,
        label: "Improcedente",
        onChange: function() {
          reclamacio.improc = !Questionnaire.call.improc;
          reclamacio.proc = false
        },
      }),
      m("br"),
      m(Checkbox, {
        className: "checkbox",
        name: 'noproc',
        checked: (!reclamacio.improc && !reclamacio.proc),
        label: "No gestionable",
        onChange: function() {
          reclamacio.improc = false;
          reclamacio.proc = false;
        },
      }),
    ]);
  }

  var preguntarResolt = function(reclamacio) {
    return m("", [
      m("p", "S'ha resolt?"),
      m(Checkbox, {
        className: "checkbox",
        name: 'solved-yes',
        checked: reclamacio.solved,
        label: "Sí",
        onChange: function() {
            reclamacio.solved = !reclamacio.solved;
        },
      }),
      m("br"),
      m(Checkbox, {
        className: "checkbox",
        name: 'solved-no',
        checked: !reclamacio.solved,
        label: "No",
        onChange: function() {
            reclamacio.solved = !reclamacio.solved;
        },
      }),
    ]);
  }

  var buttons = function(reclamacio) {
    return [
      m(Button, {
        label: "Cancel·lar",
        events: {
          onclick: function() {
            Dialog.hide({id:'fillReclama'});
          },
        },
        raised: true,
      }),
      m(Button, {
        label: "Desa",
        events: {
          onclick: function() {
            enviar(reclamacio);
            Dialog.hide({id:'fillReclama'});
            Dialog.hide({id:'settingsDialog'});
          },
        },
        disabled: (reclamacio.tag === "ASSIGNAR USUARI"),
        contained: true,
        raised: true,
      })
    ];
  }

  var emplenaReclamacio = function(tag) {
    var reclamacio = {
      "proc": false,
      "improc": false,
      "solved": true,
      "tag": tag
    }
    Dialog.show(function() { return {
      className: 'dialog-reclama',
      title: 'Reclamació:',
      backdrop: true,
      body: [
        seleccionaUsuari(reclamacio, tag),
        m("br"),
        preguntarResolt(reclamacio),
        m("br"),
        (!reclamacio.solved && m("") || tipusATR(reclamacio)),
        m("br"),
      ],
      footerButtons: buttons(reclamacio),
    };},{id:'fillReclama'});
  }
  Dialog.show(function() { return {
    className: 'card-motius',
    title: m(".card-motius-title", [
      m(".motiu", 'Motiu: '),
      m(".filter", m(Textfield, {
        className: "textfield-filter",
        label: "Escriure per filtrar",
        value: reason_filter,
        dense: true,
        onChange: function(params) {
          reason_filter = params.value
        }
      })),
    ]),
    backdrop: true,
    body: [
      m("", [
        llistaMotius(),
        m(".final-motius", [
          m("strong", "Comentaris:"),
          m(Textfield, {
            className: "textfield-comentaris",
            label: "Especifica més informació",
            multiLine: true,
            rows: 2,
            dense: true,
            value: Questionnaire.call['extra'],
            onChange: function(params) {
              Questionnaire.call['extra'] = params.value
            },
            disabled: (desar !== "Desa" || Questionnaire.call.date === ""),
          }),
        ]),
      ])
    ],
    footerButtons: [
      m(Button, {
        label: "Sortir",
        events: {
            onclick: function() {
                Dialog.hide({id:'settingsDialog'});
            },
        },
        raised: true,
      }),
      m(Button, {
        className: "save",
        label: desar,
        events: {
          onclick: function() {
            var tag = getTag(Questionnaire.call.reason);
            if (esReclamacio(tag)) {
              emplenaReclamacio(tag);
            }
            else {
              enviar();
            }
          },
        },
        border: 'true',
        disabled: (
          desar !== "Desa" ||
          Questionnaire.call.reason === "" ||
          Questionnaire.call.extra === "" ||
          Questionnaire.call.date === "" ||
          Questionnaire.call.iden === ""
        ),
      }, m(Ripple)),
    ]
  };},{id:'settingsDialog'});

}

return Questionnaire;

}();
