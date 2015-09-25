var d3module = angular.module('d3', []);

d3module.factory('d3Service', ['$document', '$q', '$rootScope',
	function($document, $q, $rootScope) {
		var d = $q.defer();
		function onScriptLoad() {
			$rootScope.$apply(function() { d.resolve(window.d3); });
		}

		var scriptTag = $document[0].createElement('script');
		scriptTag.type = 'text/javascript';
		scriptTag.async = true;

		// TODO: this should not be hard-coded.
		scriptTag.src = '/static/annotations/js/d3.min.js';
		
		scriptTag.onreadystatechange = function () {
			if (this.readyState == 'complete') onScriptLoad();
		}
		scriptTag.onload = onScriptLoad;

		var s = $document[0].getElementsByTagName('body')[0];
		s.appendChild(scriptTag);

		return {
			d3: function() { return d.promise; }
		};
}]);
