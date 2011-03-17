// jslint configuration
/*jslint browser: true */
/*global $, OpenLayers, window, verticalItemHeight, mainContentWidth, restretchExistingElements
divideVerticalSpaceEqually, reloadGraphs, show_popup, nothingFoundPopup */


function graph_type_select(event) {
    var $form, url, div;
    event.preventDefault();
    $form = $(this).parents("#graphtype-select-form");
    url = $form.attr("action");
    $.ajax({
        url: url,
        data: $form.serialize(),
        type: "POST",
        success: function (data, textStatus, xhr) {
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
        function  (data) {
            $("#map_OpenLayers_ViewPort").css("cursor", "default");
            redirect_to_area(data);
        });
}


$(document).ready(function () {
    $("input#graph-type-select-submit").click(graph_type_select);
    $("input#recalculate-submit").click(recalculate_action);
    $("#activate-adjustment-form").click(activate_adjustment_form_action);
    $("#edit-sub-form-submit").live('click', adjustment_form_submit);
});

