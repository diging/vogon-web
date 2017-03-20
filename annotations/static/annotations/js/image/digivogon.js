/**
  *  Adaptation of the digiglib.regions plugin, without the framework frills.
  */
var IDCOUNT = 40;
var isNumber = function (value) {
    return typeof value === 'number' && isFinite(value);
};

var removeSpecificRegion = function(id) {
    $('#' + id + '.' + 'CSS' + 'regionURL').remove();
    redisplay(data);
    return;
};

// remove all findregions or the last added user-defined region
var removeUserRegion = function (data) {
    if (!data.settings.isRegionVisible) {
        alert("Please turn on regions visibility!");
        return;
    }
    // remove highlights
    var selector = 'div.'+'CSS'+'highlightregion';
    var $highlights = data.$elem.find(selector);
    if ($highlights.length > 0) {
        $highlights.removeClass('CSS'+'highlightregion');
        return;
    }
    // remove findregion divs
    selector = 'div.'+'CSS'+'findregion';
    var $findregions = data.$elem.find(selector);
    if ($findregions.length > 0) {
        $findregions.remove();
        redisplay(data);
        return;
    }
    // remove most recently added user region
    selector = 'div.'+'CSS'+'regionURL';
    var $region = data.$elem.find(selector).last();
    if ($region.length > 0) {
        $region.remove();
        redisplay(data);
        return;
    }
};

// remove all manually added regions (defined through URL "rg" parameter)
var removeAllUserRegions = function (data) {
    if (!data.settings.isRegionVisible) {
        alert("Please turn on regions visibility!");
        return;
    }
    var selector = 'div.'+'CSS'+'regionURL, div.'+'CSS'+'findregion';
    var $regionDivs = data.$elem.find(selector);
    if ($regionDivs.length == 0) return;
    $regionDivs.remove();
    redisplay(data);
};

// show/hide regions
var toggleRegions = function () {
    var $elem = $('#digilib-image-container');
    var data = $elem.data('digilib');
    renderRegions(data, 1);
};

// draw a find region from coords and move into view
var regionFromCoords = function (data, coords) {
    var rect = parseCoords(data, coords);
    if (rect == null) {
        alert('invalid coordinates: ' + coords);
        return;
        }
    var attr = { 'class': 'CSS'+'findregion' };
    var item = { 'rect': rect, 'attributes': attr };
    var $regionDiv = addRegionDiv(data, item);
    var newZoomArea = centerZoomArea(data, rect);
    redisplay(data);
};

// highlight regions by id
var highlightRegions = function (data, ids) {
    if (ids == null || ids.length < 1) return;
    var selector = '#'+ids.join(',#');
    var $regions = data.$elem.find(selector);
    $regions.addClass('CSS'+'highlightregion');
    if (ids.length == 1) {
        var rect = $regions.data('rect');
        centerZoomArea(data, rect);
        redisplay(data);
    }
};

// find coordinates and display as new region
var findCoords = function (data) {
    var $elem = data.$elem;
    var findSelector = '#'+'CSS'+'regionFindCoords';
    if (isOnScreen(data, findSelector)) return; // already onscreen
    var html = '\
        <div id="'+'CSS'+'regionFindCoords" class="'+'CSS'+'keep '+'CSS'+'regionInfo">\
            <div>coordinates to find:</div>\
            <form class="'+'CSS'+'form">\
                <div>\
                    <input class="'+'CSS'+'input" name="coords" type="text" size="30"/> \
                </div>\
                <input class="'+'CSS'+'submit" type="submit" name="sub" value="Ok"/>\
                <input class="'+'CSS'+'cancel" type="button" value="Cancel"/>\
            </form>\
        </div>';
    var $info = $(html);
    $info.appendTo($elem);
    var $form = $info.find('form');
    var $input = $info.find('input.'+'CSS'+'input');
    // handle submit
    $form.on('submit', function () {
        var coords = $input.val();
        actions.regionFromCoords(data, coords);
        withdraw($info);
        return false;
        });
    // handle blur
    $input.on('blur', function () {
        withdraw($info);
        });
    // handle cancel
    $form.find('.'+'CSS'+'cancel').on('click', function () {
        withdraw($info);
        });
    $info.fadeIn();
    centerOnScreen(data, $info);
    $input.focus();
};

// find a region by text data and higlight it
var findData = function (data) {
    var $elem = data.$elem;
    var findSelector = '#'+'CSS'+'regionFindData';
    if (isOnScreen(data, findSelector)) return; // already onscreen
    var options = filteredOptions(data, 'regionHTML');
    var html = '\
        <div id="'+'CSS'+'regionFindData" class="'+'CSS'+'keep '+'CSS'+'regionInfo">\
            <div>Find object:</div>\
            <form class="'+'CSS'+'form">\
                <div>\
                    <select class="'+'CSS'+'finddata">\
                    <option/>\
                    '+options+'\
                    </select>\
                </div>\
                <input class="'+'CSS'+'input" name="data" type="text" size="30" /> \
                <input class="'+'CSS'+'submit" type="submit" name="sub" value="Ok"/>\
                <input class="'+'CSS'+'cancel" type="button" value="Cancel"/>\
            </form>\
        </div>';
    var $info = $(html);
    $info.appendTo($elem);
    var $form = $info.find('form');
    var $input = $info.find('input.'+'CSS'+'input');
    var $select = $info.find('select');
    var $options = $select.find('option');
    // callback if a region is selected by name
    var findRegion = function () {
        var id = [$select.val()];
        withdraw($info);
        actions.highlightRegions(data, id);
        return false;
        };
    // adapt dropdown, show only matching entries
    var filterOptions = function (filter) {
        var options = filteredOptions(data, 'regionHTML', filter);
        $select.empty();
        $select.append($(options));
        };
    // handle submit
    $form.on('submit', findRegion);
    $select.on('change', findRegion);
    $input.on('keyup', function (event) {
        // ugly: we need setTimeout here to get an updated val();
        window.setTimeout(filterOptions, 100, $input.val());
        if (event.keyCode == '38' || event.keyCode == '40') { // arrows
            $select.focus();
        }
        });
    // handle cancel
    $form.find('.'+'CSS'+'cancel').on('click', function () {
        withdraw($info);
        });
    $info.fadeIn();
    centerOnScreen(data, $info);
    $input.focus();
};

// make a coords string
var packCoords = function (rect, sep) {
    if (sep == null) sep = ','; // comma as default separator
    return [
    cropFloatStr(rect.x),
    cropFloatStr(rect.y),
    cropFloatStr(rect.width),
    cropFloatStr(rect.height)
    ].join(sep);
};

// create a rectangle from a coords string
var parseCoords = function (data, coords) {
    var $elem = $('#digilib-image-container');
    var geom = $elem.digilib.apply($elem, ['getGeom']);

    var pos = coords.match(/[0-9.]+/g); // TODO: check validity?
    if (pos == null) {
        return null;
        }
    var rect = geom.rectangle(pos[0], pos[1], pos[2], pos[3]);
    if (!isNumber(rect.x) || !isNumber(rect.y)) {
        return null;
        }
    if (!rect.getArea()) {
        var pt = rect.getPosition();
        rect.width = data.settings.regionWidth;
        rect.height = rect.width;
        rect.setCenter(pt);
        }
    return rect;
};

// create a new regionDiv and add it to data.$elem
var newRegionDiv = function (data, attr) {
    var cls = 'CSS'+'region';
    var $regionDiv = $('<div class="'+cls+'"/>');
    addRegionAttributes(data, $regionDiv, attr);
    data.$elem.append($regionDiv);
    return $regionDiv;
};

// copy attributes to a region div
var addRegionAttributes = function (data, $regionDiv, attributes) {
    if (attributes == null) return;
    if (attributes['class']) {
        $regionDiv.addClass(attributes['class']);
        delete attributes['class'];
    }
    if (attributes['href']) {
        $regionDiv.data('href', attributes['href']);
        delete attributes['href'];
    }
    if (attributes['title']) {
        $regionDiv.data('text', attributes['title']);
    }
    // create an ID if none exists
    if (!attributes['id']) {
        attributes['id'] = 'CSS'+IDCOUNT.toString(16);
        IDCOUNT += 1;
    }
    $regionDiv.attr(attributes);
};

// set region number
var addRegionNumber = function (data, $regionDiv, index) {
    if (!data.settings.showRegionNumbers) return;
    if (!isNumber(index)) return;
    var $number = $('<a class="'+'CSS'+'regionnumber">'+index+'</a>');
    $regionDiv.append($number);
    return $regionDiv;
};

// construct a region from a rectangle
var addRegionDiv = function (data, item) {
    var $regionDiv = newRegionDiv(data, item.attributes);
    var settings = data.settings;
    // add region number
    addRegionNumber(data, $regionDiv, item.index);
    // add inner HTML
    if (item.inner) {
        $regionDiv.append(item.inner);
    }
    // store the coordinates in data
    $regionDiv.data('rect', item.rect);

    // trigger a region event on click
    $regionDiv.on('click.dlRegion', function (event) {
        $(data).trigger('regionClick', [$regionDiv]);
    });
    return $regionDiv;
};

// create regions from a Javascript array of items
var createRegionsFromJS = function (data, items) {
    $.each(items, function (index, item) {
        addRegionDiv(data, item);
        });
};

// create regions from a JSON array of items (x,y,w,h,title,index)
var createRegionsFromJSON = function (data, items) {
  var ww = data.settings.regionWidth;
  $.each(items, function (index, item) {
    addRegionDiv(data, {
      rect: geom.rectangle(item.x, item.y, item.w || ww, item.h || ww),
      attributes: {'class': 'CSS'+"regionJSON "+'CSS'+"overlay", title: item.title },
      index: item.index || index+1
      });
    });
};

// create regions from URL parameters
var createRegionsFromURL = function (data) {
    var userRegions = unpackRegions(data);
    if (!userRegions) return;
    createRegionsFromJS(data, userRegions);
};

// create regions from HTML
var createRegionsFromHTML = function (data) {
    // regions are defined in "area" tags
    var $areas = data.$elem.find(data.settings.areaSelector);
    $areas.each(function (index, area) {
        var $area = $(area);
        // the "title" attribute contains the text for the tooltip
        var title = $area.attr('title');
        // the "coords" attribute contains the region coords (0..1)
        var coords = $area.attr('coords');
        // create the rectangle
        var rect = parseCoords(data, coords);
        if (rect == null) {
            return console.error('bad coords in HTML:', title, coords);
        }
        // mark div class as regionHTML
        var cls = $area.attr('class') || '';
        cls += ' '+'CSS'+'regionHTML '+'CSS'+'overlay';
        var attr = {'class': cls};
        // copy attributes
        for (var n in data.settings.regionAttributes) {
            attr[n] = $area.attr(n);
        }
        // copy inner HTML
        var $inner = $area.contents().clone();
        if (attr.href != null) {
            // wrap contents in a-tag
            var $a = $('<a href="'+attr.href+'"/>');
            $inner = $a.append($inner);
        }
        var item = {'rect': rect, 'attributes': attr, 'inner': $inner};
        var $regionDiv = addRegionDiv(data, item);
    });
    // $areas.removeAttr('id');
    $areas.remove();
};

// select region divs (HTML or URL)
var getRegions = function (data, selector) {
    var $regions = data.$elem.find('div.'+'CSS'+selector);
    return $regions;
};

// create a filter text matcher
var getFilterRE = function (filter) {
    if (!filter) return null;
    // sanitize and split
    var parts = filter.replace(/([\\\(\)\-\!.+?*])/g, '\\$1').split(/\s+/);
    // match all parts anywhere in optiontext
    var regexparts = $.map(parts, function(part) {
        // one lookahead for each filter part
        return '(?=.*'+part+')';
        });
    var RE = new RegExp(regexparts.join(''), 'i');
    return RE;
    };

// make HTML option from regions text data
var filteredOptions = function (data, selector, filter) {
    var options = [];
    var sort = data.settings.regionSortString;
    var RE = getFilterRE(filter);
    var createOption = function (index, region) {
        var $region = $(region);
        var rect = $region.data('rect');
        if (rect == null) return;
        // var coords = packCoords(rect, ',');
        var text = $region.data('text');
        if (text == null) {
            text = $region.text();
            }
        if (RE == null || text.match(RE)) {
            var id = $region.attr('id');
            var sortstring = $region.data('sort')
                || (typeof sort === 'function')
                    ? sort(text)
                   : text;
            var option = '<option value="'+id+'">'+text+'</option>';
            options.push([sortstring, option]);
            }
        };
    var $regions = getRegions(data, selector);
    $.each($regions, createOption);
    options.sort(function (a, b) {
        return a[0].localeCompare(b[0]);
        });
    var sorted = $.map(options, function (str, index) {
        return str[1];
        });
    // prepend an empty option
    return sorted.join('');
};

// show a region on top of the scaler image
// TODO: faster rendering for large numbers of regions?
var renderRegion = function (data, $regionDiv, anim) {
    var zoomArea = data.zoomArea;
    var rect = $regionDiv.data('rect').copy();
    if (zoomArea.overlapsRect(rect) && !rect.containsRect(zoomArea)) {
        rect.clipTo(zoomArea);
        if (data.imgTrafo) {
            var screenRect = data.imgTrafo.transform(rect);

            // console.debug("renderRegion: pos=",geom.position(screenRect));
            if (anim) {
                $regionDiv.fadeIn();
            } else{
                $regionDiv.show();
            }
            // adjustDiv sets wrong coords when called BEFORE show()
            screenRect.adjustDiv($regionDiv);
        }
    } else {
        if (anim) {
            $regionDiv.fadeOut();
        } else{
            $regionDiv.hide();
        }
    }
};

// show regions
var renderRegions = function (data, anim) {
    var render = function (index, region) {
        renderRegion(data, $(region), anim);
    };
    var $regions = getRegions(data, 'region')
    $regions.each(render);
};

// read region data from URL parameters
var unpackRegions = function (data) {
    var rg = data.settings.rg;
    if (rg == null) return [];
    var coords = rg.split(",");
    var regions = $.map(coords, function (coord, index) {
        var pos = coord.split("/", 4);
        var rect = geom.rectangle(pos[0], pos[1], pos[2], pos[3]);
        var attr = {'class': 'CSS'+"regionURL "+'CSS'+"overlay"};
        var item = {'rect': rect, 'index': index+1, 'attributes': attr};
        return item;
        });
    return regions;
};

// pack user regions array into a URL parameter string
var packRegions = function (data) {
    var $regions = getRegions(data, 'regionURL');
    if ($regions.length == 0 || !data.settings.processUserRegions) {
        data.settings.rg = null;
        return;
    }
    var pack = function (region, index) {
        var $region = $(region);
        var rect = $region.data('rect');
        var packed = packCoords(rect, '/');
        return packed;
        };
    var coords = $.map($regions, pack);
    var rg = coords.join(',');
    data.settings.rg = rg;
    console.debug('pack regions:', rg);
};

// zoom in, displaying the region in the middle of the screen
var zoomToRegion = function (data, $regionDiv) {
    var settings = data.settings;
    var rect = $regionDiv.data('rect');
    var za = rect.copy();
    var factor = settings.regionAutoZoomFactor;
    za.width  *= factor;
    za.height *= factor;
    // var screen = getFullscreenRect(data);
    za.setProportion(1, true); // avoid extreme zoomArea proportions
    za.setCenter(rect.getCenter()).stayInside(FULL_AREA);
    setZoomArea(data, za);
    redisplay(data);
};

// reload display after a region has been added or removed
var redisplay = function (data) {
    packRegions(data);
    // redisplay(data);
};

// event handler, gets called when a newRegion event is triggered
var handleNewRegion = function (evt, $regionDiv) {
    //
    // var data = this;
    // var settings = data.settings;
    //
    // if (typeof settings.onNewRegion === 'function') {
    //     // execute callback
    //     return settings.onNewRegion(data, $regionDiv);
    //     }
    // if (typeof settings.onNewRegion === 'string') {
    //     // execute action
    //     return actions[settings.onNewRegion](data, $regionDiv);
    // }
};

// event handler, gets called when a regionClick event is triggered
var handleRegionClick = function (evt, $regionDiv) {
    var data = this;
    var settings = data.settings;
    // console.debug("regions: handleRegionClick", $regionDiv);
    // if ($regionDiv.data('href')) {
    //     // follow the href attribute of the region area
    //     window.location = $regionDiv.data('href'); //TODO: how about target?
    // }
    // if (typeof settings.onClickRegion === 'function') {
    //     // execute callback
    //     return settings.onClickRegion(data, $regionDiv);
    // }
    // if (typeof settings.onClickRegion === 'string') {
    //     // execute action
    //     return actions[settings.onClickRegion](data, $regionDiv);
    // }
};


// event handler, sets buttons and shows regions when scaler img is reloaded
var handleUpdate = function (evt) {
    var data = this;
    var settings = data.settings;
    renderRegions(data);
};
