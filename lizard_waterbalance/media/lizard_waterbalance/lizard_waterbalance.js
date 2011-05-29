// jslint configuration
/*jslint browser: true */
/*global $, OpenLayers, window, verticalItemHeight, mainContentWidth, restretchExistingElements
divideVerticalSpaceEqually, reloadGraphs, show_popup, nothingFoundPopup */


function graph_type_select(event) {
    var $form, url, div;
    event.preventDefault();
    $form = $(this).parents("#graphtype-select-form");
    url = $form.attr("action");
    
    $button = $("#graph-type-select-submit");
    original_text = $button.attr("value");
    $button.attr("value", "Aan het berekenen...");
    $button.attr("disabled", "true");
    $button.effect("pulsate", {"times": 2}, 2000);
    
    $.ajax({
        url: url,
        data: $form.serialize(),
        type: "POST",
        success: function (data, textStatus, xhr) {
            $button.attr("value", original_text);
            $button.removeAttr("disabled");
            $('div#evenly-spaced-vertical .vertical-item').remove();
            $.each(data, function (index, val) {
                // console.log(val);
                div = $("<div/>").addClass('vertical-item').addClass('img-use-my-size');
                div.append($("<a/>").addClass('replace-with-image').attr('href', val).attr(
                    'data-errormsg', 'Waarschijnlijk is niet alle data ingevuld'));
                // $('div#evenly-spaced-vertical').append(div);
                div.insertBefore('#adjustment-form');
            });
            restretchExistingElements();
        },
        error: function (data, textStatus, xhr) {
            $button.attr("value", original_text);
            $button.removeAttr("disabled");
            $('div#evenly-spaced-vertical .vertical-item').remove();
        }
    });
}


function recalculate_action(event) {
    var $form, url, $button, original_text;
    event.preventDefault();
    $form = $("#recalculate-form");
    $button = $("#recalculate-submit");
    url = $form.attr("action");
    original_text = $button.attr("value");
    $button.attr("value", "Aan het berekenen...");
    $button.attr("disabled", "true");
    $button.effect("pulsate", {"times": 2}, 2000);
    $.ajax({
        url: url,
        data: $form.serialize(),
        type: "POST",
        success: function (data, textStatus, xhr) {
            $button.attr("value", original_text);
            $button.removeAttr("disabled");
            restretchExistingElements();
        }
    });
}


function activate_adjustment_form_action(event) {
    var url;
    event.preventDefault();
    url = $("#activate-adjustment-form").attr("href");
    $("#adjustment-form").load(url + " #form", function () {
        $("#adjustment-form").show();
        $("#adjustment-form").addClass("double-vertical-item");
        divideVerticalSpaceEqually();
        reloadGraphs();
        $("ul.tabs").tabs("div.panes > div", {effect: 'ajax'});
    });
}


function adjustment_form_submit(event) {
    var $form, url, $button, original_text;
    event.preventDefault();
    $form = $("#edit-sub-form");
    $button = $("#edit-sub-form-submit");
    url = $form.attr("action");
    original_text = $button.attr("value");
    $button.attr("value", "Bezig met opslaan en met herberekenen grafiekdata...");
    $button.attr("disabled", "true");
    $button.effect("pulsate", {"times": 2}, 2000);
    $.ajax({
        url: url,
        data: $form.serialize(),
        type: "POST",
        success: function (data, textStatus, xhr) {
            $button.attr("value", original_text);
            $button.removeAttr("disabled");
            reloadGraphs();
            $("#edit-sub-form").parent().html(data);
        },
        error: function (data, textStatus, xhr) {
            $button.attr("value", original_text);
            $button.removeAttr("disabled");
            $("#edit-sub-form").parent().html(data);
        }
    });
}


function single_edit_link_click(event) {
    // Also used for the single edit page's back link, btw.
    var url;
    event.preventDefault();
    //console.log($(this).attr("href"));
    $("#multiple").load($(this).attr("href"));
}


function redirect_to_area(data) {
    if (data !== "" && data !== undefined) {
        window.location = data;
    }
    else {
        nothingFoundPopup();
    }
}

function make_graphs_wide(event) {
	$("#graph_window").css("overflow","scroll");
	$("#evenly-spaced-vertical").css("width",6000);
	$("input#graph-type-select-submit").click();	
}

function divideVerticalSpaceEqually() {
/* 
Overwrites Lizard function, to ensure space below the graphs for scrollbar
TO DO: change this overwrite of function
*/
  var space_below = 20; 
  var numberOfItems, numberOfDoubleItems;
  numberOfItems = $('#evenly-spaced-vertical > .vertical-item').length;
  numberOfDoubleItems = $('#evenly-spaced-vertical > .double-vertical-item').length;
  verticalItemHeight = Math.floor(
  ((mainContentHeight-space_below) / (numberOfItems + 2 * numberOfDoubleItems))) - 1;
  $('#evenly-spaced-vertical > .vertical-item').height(verticalItemHeight);
  $('#evenly-spaced-vertical > .double-vertical-item').height(2 * verticalItemHeight);
} 


function waterbalance_area_click_handler(x, y, map) {
    $("#map_OpenLayers_ViewPort").css("cursor", "progress");
    $.get(
        "/waterbalance/area_search/", { x: x, y: y },
        function  (data) {
            $("#map_OpenLayers_ViewPort").css("cursor", "default");
            redirect_to_area(data);
        });
}


$(document).ready(function () {
    $("input#graph-type-select-submit").click(graph_type_select);
    $("input#recalculate-submit").click(recalculate_action);
    $("#activate-adjustment-form").click(activate_adjustment_form_action);
    $("#graph-wide-button").click(make_graphs_wide);
    $("#edit-sub-form-submit").live('click', adjustment_form_submit);
    $(".edit-single-link").live('click', single_edit_link_click);
    $(".back-to-multiple").live('click', single_edit_link_click);
    $("input#graph-type-select-submit").click();
});

