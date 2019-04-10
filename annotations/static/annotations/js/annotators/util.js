if(typeof(String.prototype.trim) === "undefined")
{
    String.prototype.trim = function()
    {
        return String(this).replace(/^\s+|\s+$/g, '');
    };
}

function sleep (time) {
  return new Promise(function(resolve) {setTimeout(resolve, time)});
}

var truncateURI = function(input) {
  return input.split('/').pop();
}

var getOffsetTop = function(elem) {
    var offsetTop = 0;
    do {
      if ( !isNaN( elem.offsetTop ) )
      {
          offsetTop += elem.offsetTop;
      }
    } while( elem = elem.offsetParent );
    return offsetTop;
}

var getOffsetLeft = function( elem ) {
    var offsetLeft = 0;
    do {
      if ( !isNaN( elem.offsetLeft ) )
      {
          offsetLeft += elem.offsetLeft;
      }
    } while( elem = elem.offsetParent );
    return offsetLeft;
}

/**
  * Get a bounding box for a text selection in the '#text-content' element.
  */
var getTextPosition = function(textPosition) {
    var range = document.createRange();
    var textContainer = document.getElementById('text-content');
    var textContent = textContainer.childNodes.item(0);

    var containerRect = textContainer.getBoundingClientRect();

    range.setStart(textContent, textPosition.startOffset);
    range.setEnd(textContent, textPosition.endOffset);
    // These rects contain the client coordinates in top, left
    var rects = range.getClientRects()[0];

    return {
        top: rects.top -  containerRect.top,
        bottom: rects.bottom - containerRect.top,
        left: rects.left - containerRect.left,
        right: rects.right - containerRect.left,
        width: rects.width
    };
}

/**
  * Get a bounding box for a text position in the '#text-content' element.
  */
var getPointPosition = function(offset) {
    var range = document.createRange();

    var textContainer = document.getElementById('text-content');
    var textContent = textContainer.childNodes.item(0);

    var containerRect = textContainer.getBoundingClientRect();
    range.setStart(textContent, offset);
    range.setEnd(textContent, offset);
    // These rects contain the client coordinates in top, left
    var rects = range.getClientRects()[0];

    return {
        top: rects.top - containerRect.top,
        bottom: rects.bottom - containerRect.top,
        left: rects.left - containerRect.left,
        right: rects.right - containerRect.left,
        width: rects.width
    };
}


/**
  * Get the computed value of a style property for an element.
  */
var getStyle = function(el, styleprop){
	el = document.getElementById(el);
    var val = null;
	if(window.getComputedStyle){
        val = window.getComputedStyle(el)[styleprop];   // Firegox
        if (val == null) {
    		return document.defaultView.getComputedStyle(el, null)
                                       .getPropertyValue(styleprop);
        } else {
            return val;
        }
	} else if(el.currentStyle){
		return el.currentStyle[styleprop.encamel()];
	}
	return null;
}


var clearMouseTextSelection = function () {
    if (window.getSelection) {
        if (window.getSelection().empty) {  // Chrome
            window.getSelection().empty();
        } else if (window.getSelection().removeAllRanges) {  // Firefox
            window.getSelection().removeAllRanges();
        }
    } else if (document.selection) {  // IE?
        document.selection.empty();
    }
}

var getAbsoluteTop = function(elemId) {
    return document.getElementById(elemId).getClientRects()[0].top + window.scrollY;
}

getFormattedDate = function(isodate) {
    var date = new Date(isodate);
    var monthNames = [
        "January", "February", "March",
        "April", "May", "June", "July",
        "August", "September", "October",
        "November", "December"
      ];
      var minutes = String(date.getMinutes());
      if (minutes.length == 1) {
          minutes = '0' + minutes;
      }

      var day = date.getDate();
      var monthIndex = date.getMonth();
      var year = date.getFullYear();

      return day + ' ' + monthNames[monthIndex] + ', ' + year + ' at ' + date.getHours() + ':' + minutes;
}


getCreatorName = function(creator) {
    if (creator.id == USER_ID) {
        return 'you';
    } else {
        return creator.username;
    }
}
