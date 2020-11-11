var jsyaml = require('js-yaml');

function deyamlize(xhr) {
	return jsyaml.safeLoad(xhr.responseText);
}

module.exports = {
	deyamlize: deyamlize,
};
