
/******************************************************************************
  *         Resources!
  *****************************************************************************/
Vue.http.headers.common['X-CSRFTOKEN'] = Cookie.get('csrftoken');

var Appellation = Vue.resource(BASE_URL + '/rest/appellation{/id}');
var DateAppellation = Vue.resource(BASE_URL + '/rest/dateappellation{/id}');
var Relation = Vue.resource(BASE_URL + '/rest/relationset{/id}');
var Concept = Vue.resource(BASE_URL + '/rest/concept{/id}', {}, {
    search: {method: 'GET', url: BASE_URL + '/rest/concept/search'}
});
var RelationTemplateResource = Vue.resource(BASE_URL + '/relationtemplate{/id}/', {}, {
    create: {method: 'POST', url: BASE_URL + '/relationtemplate{/id}/create/'}
});
var ConceptType = Vue.resource(BASE_URL + '/rest/type{/id}');
var UploadStatus = Vue.resource(BASE_URL + '/upload/status/');