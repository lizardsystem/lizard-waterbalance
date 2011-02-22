// jslint configuration
/*jslint browser: true */
/*global $, OpenLayers, window, verticalItemHeight, mainContentWidth, restretchExistingElements
show_popup, nothingFoundPopup */

jQuery.fn.reverse = function() {
    return this.pushStack(this.get().reverse(), arguments);
};

$(document).ready(function() {
    $('input#apply').click(function() {
        jQuery.ajax({
            url: '/waterbalance/graphselect/',
            type: 'POST',
            dataType: 'json',
            data: $('input[type=checkbox]:checked').reverse(),
            success: function(data, textStatus, xhr) {
                $('div#evenly-spaced-vertical').html("");
                jQuery.each(data, function(index, val) {
                    // console.log(val);
                    div = $("<div/>").addClass('vertical-item').addClass('img-use-my-size');
                    div.append($("<a/>").addClass('replace-with-image').attr('href', val));
                    $('div#evenly-spaced-vertical').append(div);
                });
                restretchExistingElements();
            },
            complete: function(xhr, textStatus) {
                return;
            },
            error: function(xhr, textStatus, errorThrown) {
                return;
            }
        });
    });
});


function redirect_to_area(data) {
    if (data !== "" && data !== undefined) {
        window.location = data;
    }
    else {
        nothingFoundPopup();
    }
}


function waterbalance_area_click_handler(x, y, map) {
    $("#map_OpenLayers_ViewPort").css("cursor", "progress");
    $.get(
        "/waterbalance/area_search/", { x: x, y: y },
        function (data) {
            $("#map_OpenLayers_ViewPort").css("cursor", "default");
            redirect_to_area(data);
        });
}
