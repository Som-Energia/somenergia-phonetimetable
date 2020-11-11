var jsyaml = require('js-yaml');

function deyamlize(xhr) {
	return jsyaml.safeLoad(xhr.responseText);
}

var getCookie = function(name) {
    function escape(s) { return s.replace(/([.*+?\^$(){}|\[\]\/\\])/g, '\\$1'); }
    var match = document.cookie.match(RegExp('(?:^|;\\s*)' + escape(name) + '=([^;]*)'));
    return match ? match[1] : ":";
}

module.exports = {
	deyamlize: deyamlize,
	getCookie: getCookie,
};
