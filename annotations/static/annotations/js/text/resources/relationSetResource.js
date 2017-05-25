/**
  * Each Concept has a specific Type, usually from the CIDOC-CRM.
  */
angular.module('annotationApp').factory('RelationSet', function($resource) {
    return $resource(BASE_URL + '/rest/relationset/:id/', {
        text: TEXTID,
        thisuser: true,
        project: PROJECTID
    }, {
        list: {
            method: 'GET',
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
