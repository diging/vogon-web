/* function onLoad() {
   var createdBy = getQueryVariable("createdBy");
   var occursIn = getQueryVariable("occursIn");
   var createdAfter = getQueryVariable("createdAfter");
   var createdAfter = getQueryVariable("createdBefore");
   var createdAfter = getQueryVariable("terminal_nodes");
   var createdAfter = getQueryVariable("project");
   var page = getQueryVariable("page");
   var e = document.getElementByClass("fqs");
   e.value = value;

   var url = "http://127.0.0.1:8000/relations/?createdBy="+ createdBy + "&occursIn=" + occursIn +  "&createdAfter=" + createdAfter + "&createdBefore=" + createdBefore + "&terminal_nodes=" + terminal_nodes + "&project=" + project;
   var element = document.getElementByClass("fqs");
   element.setAttribute("href",url).replace(page, "");
} */

 /*document.querySelectorAll('.fqs')
    .forEach((el) => el.attributes.href.value += window.location.search.replace("?", "&"));*/


/* var a = document.querySelectorAll('.fqs');
$a.onclick( function(){
    var url = new URL(window.location);
    var params = new URLSearchParams(url.search);
    console.log("This works");
    params.delete("page");
    am = params.toString()
    window.location.replace ( "http://www.example.com/anotherpage.html" );
} */
