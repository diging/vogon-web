/**
  * An Appellation is a text annotation by which a user indicates that a
  *  specific phrase or passage refers to a particular concept.
  */
angular.module('annotationApp').factory('Appellation', function($resource) {
  return $resource('/rest/appellation/:id/', {
      text: TEXTID,
      thisuser: true
  }, {
      list: {
          method: 'GET',
          cache: true,
          headers: {'Content-Type': 'application/json'}
      },
      save: {
          method: 'POST',
          headers: {'Content-Type': 'application/json'}
      }
  });
});
