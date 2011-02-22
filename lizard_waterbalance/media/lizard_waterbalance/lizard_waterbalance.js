// jslint configuration
/*jslint browser: true */
/*global $, OpenLayers, window, verticalItemHeight, mainContentWidth, restretchExistingElements
show_popup, nothingFoundPopup */


function graph_type_select(event) {
    // Reload graphs
    var $form, url;
    event.preventDefault();
    $form = $(this).parents("#graphtype-select-form");
    url = $form.attr("action");
    $.ajax({
        url: url,
        data: $form.serialize(),
        type: "POST",
        success: function(data, textStatus, xhr) {
            $('div#evenly-spaced-vertical').html("");
            jQuery.each(data, function(index, val) {
                // console.log(val);
                div = $("<div/>").addClass('vertical-item').addClass('img-use-my-size');
                div.append($("<a/>").addClass('replace-with-image').attr('href', val));
                $('div#evenly-spaced-vertical').append(div);
            });
            restretchExistingElements();
        }});
}


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


$(document).ready(function() {
    $("input#graph-type-select-submit").click(graph_type_select);
});

