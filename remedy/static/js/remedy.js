/* global window, jQuery, google */
/**
 * Creates standard JavaScript utilities in the window.Remedy namespace.
 * 
 * @param  {Window} global The window.
 * @param  {jQuery} $      The jQuery object.
 */
;(function (global, $) {
	'use strict';

	/**
	 * The global namespace for RAD Remedy utilities.
	 * @type {Object}
	 */
	global.Remedy = global.Remedy || {};

	/**
	 * Hides the form-group div that contains the specified element.
	 *
	 * @param  {String} elemId The ID of the element whose form group
	 *                         should be hidden.
	 */
	global.Remedy.hideFormGroup = function (elemId) {
		$(function () {
			var $formGroup = $('#' + elemId).parentsUntil('div.form-group').parent();

			// Make sure we're actually hiding a form group - we don't want to
			// mess something up by hiding the entire page
			if ($formGroup.hasClass('form-group')) {
				$formGroup.hide();
			}
		});
	};

	/**
	 * Converts the specified input element to a Bootstrap Multiselect element.
	 * 
	 * @param  {String} elemId  The ID of the input element to convert.
	 */
	global.Remedy.makeBootstrapMultiselect = function (elemId) {
		$(function () {
			var $elem = $('#' + elemId);

			// Figure out what we're referring to
			var singularNoun = 'option';
			var pluralNoun = 'options';

			if ($elem.data('noun')) {
				singularNoun = $elem.data('noun');
			}

			if ($elem.data('nounplural')) {
				pluralNoun = $elem.data('nounplural');
			}

			// Figure out the filter placeholder
			var filterPlaceholder = 'Search ' + pluralNoun;

			$elem.multiselect({
				buttonWidth: '100%',
				maxHeight: 300,
				enableClickableOptGroups: true,
				includeSelectAllOption: false,
				enableFiltering: true,
				enableCaseInsensitiveFiltering: true,
				filterPlaceholder: filterPlaceholder,
				templates: {
					filter: '<li class="multiselect-item filter"><div class="input-group"><input class="form-control multiselect-search" type="text" aria-label="' + filterPlaceholder + '"></div></li>',
          filterClearBtn: '<span class="input-group-btn"><button class="btn btn-default multiselect-clear-filter" type="button" title="Clear filter"><span class="glyphicon glyphicon-remove-circle" aria-hidden="true"></span><span class="sr-only">Clear filter</span></button></span>'
				},
				buttonText: function(options, select) {
          if (options.length === 0) {
          	// Use either the plural or singular noun
          	// depending on if the selection supports multiple
          	if ($(select).prop('multiple')) {
          		return 'No ' + pluralNoun + ' selected';
          	}
          	else {
          		return 'No ' + singularNoun + ' selected';
          	}
          }
          else if (options.length > 3) {
            return options.length.toString() + ' ' + pluralNoun + ' selected';
          }
          else {
          	// Build a comma-separated list of the selections
          	var labels = [];
            options.each(function() {
            	if ($(this).attr('label')) {
                labels.push($(this).attr('label'));
              }
              else {
              	labels.push($(this).html());
              }
             });
            return labels.join(', ') + '';
         	}
        }
			});
		});
	};

	/**
	 * Sets the location coordinates on the specified latitude/longitude values
	 * based on the provided new values.
	 * 
	 * @param {jQuery} $latitude  The latitude field to update.
	 * @param {jQuery} $longitude The longitude field to update.
	 * @param {Object} coords     The coordinates to use (with latitude/longitude properties).
	 */
	var setLocationCoordinates = function($latitude, $longitude, coords) {
		if (coords) {
			// Truncate latitude/longitude to 5 digits
			$latitude.val(coords.latitude.toFixed(5));
			$longitude.val(coords.longitude.toFixed(5));
		}
		else {
			$latitude.val('');
			$longitude.val('');
		}
	};

	/**
	 * Validates the current state of the autocomplete by adding/hiding
	 * validation icons depending on if there is text in the autocomplete
	 * and there are corresponding latitude/longitude values.
	 *
	 * Also updates the 'lastval' data field on the autocomplete to aid
	 * in detection of changes.
	 * 
	 * @param {jQuery} $autoComp  The autocomplete field to validate/update.
	 * @param {jQuery} $latitude  The latitude field to update.
	 * @param {jQuery} $longitude The longitude field to update.
	 */
	var validateAutoComplete = function($autoComp, $latitude, $longitude) {
		// Store the last value in the field
		$autoComp.data('lastval', $autoComp.val());

		// Get the containing form group
		var $fieldGroup = $autoComp.parents('.form-group').first();

		if ($fieldGroup.length === 0) {
			return;
		}

		// Make sure the field group has feedback
		$fieldGroup.addClass('has-feedback');

		// Find the feedback icon/label and exit out if there isn't one.
		var $feedbackIcon = $fieldGroup.find('.form-control-feedback');
		var $feedbackLabel = $fieldGroup.find('.js-feedback-label');

		if ($feedbackIcon.length === 0 || $feedbackLabel.length === 0) {
			return;
		}

		var $geocodeButton = $fieldGroup.find('.input-group-btn');

		// We need to space out the feedback icon if we have a
		// geocoding button also visible - Bootstrap doesn't
		// natively handle feedback icons with right-side input addons
		if ($geocodeButton.length > 0) {
			$feedbackIcon.css('right', $geocodeButton.width());
		}

		// See if we have anything in the autocomplete
		if ($autoComp.val() != '') {
			// We have something in the autocomplete box, 
			// so make sure we have latitude/longitude values
			if ($latitude.val() != '' && $longitude.val() != '') {
				$fieldGroup.addClass('has-success').
					removeClass('has-warning');

				$feedbackLabel.text('A valid location was selected.');

				$feedbackIcon.addClass('glyphicon-ok').
					attr('title', 'A valid location was selected.').
					removeClass('glyphicon-warning-sign glyphicon-option-horizontal invisible');
			}
			else {
				// We're missing values - update accordingly
				$fieldGroup.addClass('has-warning').
					removeClass('has-success');

				$feedbackLabel.text('Please select a location.');

				$feedbackIcon.addClass('glyphicon-warning-sign').
					attr('title', 'Please select a location.').
					removeClass('glyphicon-ok glyphicon-option-horizontal invisible');
			}
		}
		else {
			// Nothing selected - clear out any warnings
			$fieldGroup.removeClass('has-success has-warning');
			$feedbackLabel.html('');

			// We don't actually want to completely hide this glyphicon class
			// so that our spacing is consistent - use invisible so that
			// it still takes up the same amount of space
			$feedbackIcon.addClass('glyphicon-option-horizontal invisible').
				removeClass('glyphicon-ok glyphicon-warning-sign');
		}
	};

	/**
	 * Updates the specified button for geolocation to be
	 * enabled or disabled and toggles its child Glyphicon
	 * between a crosshairs and an hourglass.
	 * 
	 * @param  {jQuery}  $button    The button to update.
	 * @param  {Boolean} isDisabled Indicates whether the button should be
	 *                              enabled or disabled.
	 */
	var updateGeolocationButton = function($button, isDisabled) {
		$button.prop('disabled', isDisabled);
		$button.children('.glyphicon').toggleClass('glyphicon-screenshot glyphicon-hourglass');		
	};

	/**
	 * Initializes a button, which, when clicked, will attempt to determine 
	 * the user's current location and update the Google Maps autocomplete field 
	 * and backing latitude/longitude fields.
	 * 
	 * @param  {String} elemId 		 The ID of the button element to trigger geolocation.
	 * @param  {String} autoCompId The ID of the element to wire up to the autocomplete.
	 * @param  {String} latId      The ID of the element that stores latitude information.
	 * @param  {String} longId     The ID of the element that stores longitude information.
	 */
	global.Remedy.geoLocationButton = function(elemId, autoCompId, latId, longId) {
		$(function() {
			var $elem = $('#' + elemId);
			var $autoComp = $('#' + autoCompId);
			var $latitude = $('#' + latId);
			var $longitude = $('#' + longId);

			// Make sure we have all necessary fields
			if (!$elem.length || !$autoComp.length || !$latitude.length || !$longitude.length) {
				return;
			}

			if ('geolocation' in navigator === false) {
				$elem.prop('disabled', true);
				$elem.attr('title', 'Your browser does not support geolocation.');
			}

			// Ensure the button is enabled
			$elem.prop('disabled', false);

			// Wire up our click event
			$elem.on('click.remedy.geolocation', function() {
				updateGeolocationButton($elem, true);

				navigator.geolocation.getCurrentPosition(
					function(position) {
						updateGeolocationButton($elem, false);
				
						$autoComp.val('My Current Location');
						setLocationCoordinates($latitude, $longitude, position.coords);

						validateAutoComplete($autoComp, $latitude, $longitude);
					}, 
					function(error) {
						updateGeolocationButton($elem, false);
						validateAutoComplete($autoComp, $latitude, $longitude);

						// Show an error for anything other than permission denied (1)
						if (error.code !== 1) {
							global.alert('Sorry, we couldn\'t determine your position.');
						}
					},
					{
						enableHighAccuracy: false,
						timeout: 20000,
						maximumAge: 0
					}
				);
			});
		});
	};

	/**
	 * Resizes the map to fit its parent using a square dimension.
	 * 
	 * @param  {jQuery} $map The jQuery selector for the map element.
	 */
	var sizeMapToParent = function($map) {
		// Get the parent width capped between 320 and 800
		var parentWidth = Math.max(320, Math.min($map.parent().width(), 800));

		$map.width(parentWidth);
		$map.height(parentWidth);
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

				// Scale the map to the size of its parent
				var $map = $('#' + mapId);
				sizeMapToParent($map);

				// Set up the maps and track the bounds
				var map = new google.maps.Map(document.getElementById(mapId));
				var bounds = new google.maps.LatLngBounds();
				var marker;
				var infoWindow;
				var i;

				// Loop through each provider
				for(i = 0; i < providers.length; i += 1)
				{
					var r = providers[i];

					// Create a marker for the provider
					marker = new google.maps.Marker({
						map: map,
						title: r.name,
						position: new google.maps.LatLng(r.latitude, r.longitude)
					});

					// Set up the div of content to display when the marker is clicked
					var contentDiv = $('<div />');
					$('<a href=\'' + r.url + '\' target=\'_blank\'><strong>' + r.name + '</strong></a><br />').appendTo(contentDiv);
					$('<addr><small>' + r.address + '</small></addr><br />').appendTo(contentDiv);
					$('<span />').html(r.desc).appendTo(contentDiv);

					infoWindow = new google.maps.InfoWindow({
						content: contentDiv.html(),
						maxWidth: 320
					});

					// Wire up the click event - we need to wrap this in a closure to ensure
					// that clicking different markers doesn't show the same provider - see:
					// https://github.com/radremedy/radremedy/issues/229#issuecomment-113010533
					google.maps.event.addListener(marker, 'click', (function(marker, infoWindow) {
						return function() {
							infoWindow.open(map, marker);
						};
					})(marker, infoWindow));

					// Extend our bounds to include this marker
					bounds.extend(marker.position);
				}

				// Fit our map to these bounds now that all markers have been included.
				map.fitBounds(bounds);

				// Resize the map in response to window changes
				google.maps.event.addDomListener(window, 'resize', function() {
					sizeMapToParent($map);

					var center = map.getCenter();
					google.maps.event.trigger(map, 'resize');
					map.setCenter(center); 
				});    		
			});

			// Indicate we found providers.
			return true;
		}
		else {
			// No providers to show - hide the map's container.
			$(function () {
				$('#' + mapId).parent().hide();
			});

			return false;
		}
	};

	/**
	 * Retrieves the first recognized Google Maps API address component
	 * type from the provided array of types.
	 * 
	 * @param  {Array} types  The array of types to search.
	 * @return {String}       The first recognized component type in the
	 *                        provided array, or an empty string if there
	 *                        was no match.
	 */
	var getAddressComponentType = function (types) {
		// Make sure we have types
		if ( !types || !types.length ) {
			return '';
		}

		// Iterate over each type and see if it's recognized
		for(var typeIdx = 0; typeIdx < types.length; typeIdx += 1) {
			var typeName = types[typeIdx];

			// See if it's one of our recognized types
			if ($.inArray(typeName, ['locality', 'administrative_area_level_2', 'administrative_area_level_1']) >= 0) {
				return typeName;
			}
		}

		// No match found.
		return '';
	};

	/**
	 * Gets a short string representing the location of the provided
	 * Google Maps API place.
	 * 
	 * @param  {google.maps.Place} place The source Google Maps API place.
	 * @return {String}       A short location string, or an empty string
	 *                        if it was not available.
	 */
	var getLocationStr = function(place) {
		var city_str = '';
		var county_str = '';
		var state_str = '';

		// Make sure we have a place with address components
		if( !place || !place.address_components || !place.address_components.length ) {
			return '';
		}

		// Now iterate over each component
		for(var compIdx = 0; compIdx < place.address_components.length; compIdx += 1) {
			var addr_comp = place.address_components[compIdx];
			var name_str = '';
			var comp_type = '';

			/* 
			 * Figure out the name string to use - prefer short_name but
			 * fall back to long_name.
			 */
			name_str = $.trim(addr_comp.short_name) || $.trim(addr_comp.long_name);

			if( !name_str ) {
				return '';
			}

			// Find the type of this address component.
			comp_type = getAddressComponentType(addr_comp.types);

			/* 
			 * Now figure out which string to update as a result (city,
			 * state, or county)
			 */
			switch (comp_type) {
				case 'locality':
					// Issue #227 - Prefer long_name to short_name
					// for cities
					name_str = $.trim(addr_comp.long_name) || name_str;

					city_str = city_str || name_str;
					break;

				case 'administrative_area_level_2':
					county_str = county_str || name_str;
					break;

				case 'administrative_area_level_1':
					state_str = state_str || name_str;
					break;
			}
		}

		// See if we have a city, and fall back to a county if we have that instead.
		var location_str = city_str || county_str || '';

		// Finally, add the state.
		if (state_str) {
			// If we already have a city or county, add a comma/space.
			if (location_str ) {
				location_str += ', ';
			}

			location_str += state_str;
		}

		return location_str;
	};

	/**
	 * Initializes a Google Maps autocomplete field and attaches the appropriate
	 * events to update the values of dependent fields.
	 * 
	 * @param  {Boolean} forAddress If true, indicates that the autocomplete should work
	 *                              on addresses instead of general regions.
	 * @param  {String} autoCompId The ID of the element to wire up to the autocomplete.
	 * @param  {String} latId      The ID of the element that stores latitude information.
	 * @param  {String} longId     The ID of the element that stores longitude information.
	 * @param  {String} locationId The ID of the element that stores short location information. Optional.
	 */
	global.Remedy.initMapsAutocomplete = function (forAddress, autoCompId, latId, longId, locationId) {
		var $autoComp = $('#' + autoCompId);
		var $latitude = $('#' + latId);
		var $longitude = $('#' + longId);
		var $location = $(); // Default to an empty selector
		var autoCompleteTypes = [];

		// See if we have a location field
		if( locationId ) {
			$location = $('#' + locationId);
		}

		// Figure out what we're autocompleting based on forAddress
		if( forAddress ) {
			autoCompleteTypes = ['address'];
		}
		else {
			autoCompleteTypes = ['(cities)'];
		}

		// Now wire stuff up once the document loads
		$(function () {
			// Wire up the initial autocomplete
			var addrAutoComplete = new google.maps.places.Autocomplete(
				($autoComp.get()[0]),
				{
					types: autoCompleteTypes
				}
			);

			// Listen to changes
			google.maps.event.addListener(addrAutoComplete, 'place_changed', function() {
				var place = addrAutoComplete.getPlace();

				// Make sure we have a place and that it has geocoding information
				if( place && place.geometry && place.geometry.location ) {

					setLocationCoordinates($latitude, $longitude, {
						latitude: place.geometry.location.lat(),
						longitude: place.geometry.location.lng()
					});

					// Also try to get the location, if we're updating that as well
					if ( $location.length > 0 ) {
						$location.val(getLocationStr(place));
					}

					// Validate the autocomplete
					validateAutoComplete($autoComp, $latitude, $longitude);
				}
				else {
					setLocationCoordinates($latitude, $longitude, null);
					$location.val('');

					// Validate the autocomplete
					validateAutoComplete($autoComp, $latitude, $longitude);					
				}
			});

			$autoComp.on('keyup input paste change', function() {
				// Clear out the current location in response to changes
				if ($(this).val() != $(this).data('lastval')) {
					setLocationCoordinates($latitude, $longitude, null);
					$location.val('');
				}

				// Validate the autocomplete - always call this so that
				// the 'lastval' data item is properly detected
				validateAutoComplete($autoComp, $latitude, $longitude);				
			});

			// Validate the initial value of the autocomplete
			validateAutoComplete($autoComp, $latitude, $longitude);
		});
	};

})(window, jQuery);