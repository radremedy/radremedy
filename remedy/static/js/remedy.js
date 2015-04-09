/**
 * Creates standard JavaScript utilities in the window.Remedy namespace.
 * 
 * @param  {Window} global The window.
 * @param  {jQuery} $      The jQuery object.
 */
;(function (global, $) {

	/**
	 * The global namespace for RAD Remedy utilities.
	 * @type {Object}
	 */
	global.Remedy = global.Remedy || {};

	/**
	 * Hides the control-group div that contains the specified element.
	 *
	 * @param  {String} elemId The ID of the element whose control group
	 *                         should be hidden.
	 */
	global.Remedy.hideControlGroup = function (elemId) {
		$(function () {
			$("#" + elemId).parentsUntil("div.control-group").parent().hide();
		});
	};

	/**
	 * Converts the specified input element to a Select2-based item.
	 * 
	 * @param  {String} elemId  The ID of the input element to convert.
	 */
	global.Remedy.makeSelect2 = function (elemId) {
		$(function () {
			var $elem = $("#" + elemId);

			// Store the value for initialization
			var selectVal = $elem.val();

			$elem.select2({
				width: 'element'
			}).val(selectVal);
		});
	};

	/**
	 * Renders a Google map containing the specified providers, or hides
	 * it in the event that no providers have been specified.
	 * 
	 * @param  {String} mapId     The ID of the map element.
	 * @param  {Array}  providers The array of providers to show in the map.
	 *                            Each provider should have the properties
	 *                            name, latitude, longitude, address, url, and desc.
	 *
	 * @returns {Boolean} True if providers were found, false otherwise.
	 */
	global.Remedy.showProviderMap = function (mapId, providers) {
		// Make sure we have providers to show.
		if ( providers.length ) {
			$(function () {
				// Set up the maps and track the bounds
		    var map = new google.maps.Map(document.getElementById(mapId));
		    var bounds = new google.maps.LatLngBounds();

		    // Loop through each provider
		    for(i = 0; i < providers.length; i += 1)
		    {
		  		var r = providers[i];

		  		// Create a marker for the provider
		  		var marker = new google.maps.Marker({
		      	map: map,
		      	title: r.name,
		      	position: new google.maps.LatLng(r.latitude, r.longitude)
		  		});

		  		// Set up the div of content to display when the marker is clicked
		  		var contentDiv = $("<div />");
		  		$("<a href='" + r.url + "' target='_blank'><strong>" + r.name + "</strong></a><br />").appendTo(contentDiv);
		  		$("<addr><small>" + r.address + "</small></addr><br />").appendTo(contentDiv);
		  		$("<span />").html(r.desc).appendTo(contentDiv);

		  		var infoWindow = new google.maps.InfoWindow({
		      	content: contentDiv.html(),
		      	maxWidth: 320
		  		});

		  		// Wire up the click event
		  		google.maps.event.addListener(marker, 'click', function() {
		      	infoWindow.open(map, marker);
		  		});

		  		// Extend our bounds to include this marker
		    	bounds.extend(marker.position);
		    }

    		// Fit our map to these bounds now that all markers have been included.
    		map.fitBounds(bounds);
			});

			// Indicate we found providers.
			return true;
		}
		else {
			// No providers to show - hide the map's container.
			$(function () {
				$("#" + mapId).parent().hide();
			});

			return false;
		}
	};

})(window, jQuery);