/**
  * This app provides the text annotation interface in the text view.
  */
var app = angular.module('annotationApp', ['ngResource']);
app.config(function($httpProvider){
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});
