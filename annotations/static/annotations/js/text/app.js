

/**
  * This app provides the text annotation interface in the text view.
  */
var app = angular.module('annotationApp', ['ngResource', 'ui.bootstrap', 'ngCookies']);
app.config(function($httpProvider){
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});

app.filter('truncate', function(){
 return function(input){
   if(!angular.isString(input)) return;
   return input.split('/').pop();
 }
});
