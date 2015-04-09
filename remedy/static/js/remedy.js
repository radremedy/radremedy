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
	 * @param {String} elemId The ID of the element whose control group
	 *                        should be hidden.
	 */
	global.Remedy.hideControlGroup = function(elemId) {
		$(function () {
			$("#" + elemId).parentsUntil("div.control-group").parent().hide();
		});
	};

})(window, jQuery);