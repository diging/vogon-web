/**
  * An Appellation is a text annotation by which a user indicates that a
  *  specific phrase or passage refers to a particular concept.
  */
angular.module('annotationApp').factory('Appellation', function($resource) {
  return $resource(BASE_URL + '/rest/appellation/:id/', {
      text: TEXTID,
      thisuser: true,
      project: PROJECTID
  }, {
      list: {
          method: 'GET',
          cache: true,
          isArray: false,
          headers: {'Content-Type': 'application/json'}
      },
      query: {
          method: 'GET',
          isArray: false,
          headers: {'Content-Type': 'application/json'}

      },
      save: {
          method: 'POST',
          headers: {'Content-Type': 'application/json'}
      }
  });
});
