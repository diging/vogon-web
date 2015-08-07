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
		scriptTag.src = 'http://d3js.org/d3.v3.min.js';
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


// $(document).ready(function() {
//
// 	var width = 250,
// 	    height = 120;
//
// 	var color = d3.scale.category20();
//
// 	var force = d3.layout.force()
// 	    .charge(-50)
// 	    .linkDistance(100)
// 	    .size([width, height]);
//
// 	var svg = d3.select("#network").append("svg")
// 	    .attr("width", width)
// 	    .attr("height", height);
//
// 	var graph = {
// 		nodes: [
// 			{name: "Bob", group: 1},
// 			{name: "Joe", group: 2},
// 			{name: "James", group: 1},
// 		],
// 		links: [
// 			{"source":1,"target":0,"value":1},
// 			{"source":2,"target":0,"value":1}
// 		]
// 	}
//
// 	force
// 	  .nodes(graph.nodes)
// 	  .links(graph.links)
// 	  .start();
//
// 	var link = svg.selectAll(".link")
// 	  .data(graph.links)
// 	.enter().append("line")
// 	  .attr("class", "link")
// 	  .style("stroke-width", function(d) { return Math.sqrt(d.value); });
//
// 	var node = svg.selectAll(".node")
// 	  .data(graph.nodes)
// 	.enter().append("circle")
// 	  .attr("class", "node")
// 	  .attr("r", 8)
// 	  .style("fill", function(d) { return color(d.group); })
// 	  .call(force.drag);
//
// 	node.append("title")
// 	  .text(function(d) { return d.name; });
//
// 	force.on("tick", function() {
// 	link.attr("x1", function(d) { return d.source.x; })
// 	    .attr("y1", function(d) { return d.source.y; })
// 	    .attr("x2", function(d) { return d.target.x; })
// 	    .attr("y2", function(d) { return d.target.y; });
//
// 	node.attr("cx", function(d) { return d.x; })
// 	    .attr("cy", function(d) { return d.y; });
// 	});
// });
