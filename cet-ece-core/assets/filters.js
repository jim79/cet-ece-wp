/**
 * Instant filters for the faculty directory, the labs list and publications.
 *
 * Without JavaScript the forms reload the page and the server filters. With it,
 * a page that holds the complete list (data-complete="1") filters in place and
 * keeps the choices in the address, so a filtered view can be shared. This is
 * also what makes the filters work on the static copy of the site.
 */
( function () {
	'use strict';

	function has( list, value ) {
		return ( ' ' + ( list || '' ) + ' ' ).indexOf( ' ' + value + ' ' ) > -1;
	}

	function text( el, value ) {
		return el.textContent.toLowerCase().indexOf( value.toLowerCase() ) > -1;
	}

	// Field name -> test for one item.
	var tests = {
		f_q: text,
		f_des: function ( el, v ) { return el.dataset.des === v; },
		f_area: function ( el, v ) { return has( el.dataset.areas, v ); },
		l_type: function ( el, v ) { return el.dataset.type === v; },
		l_prog: function ( el, v ) { return has( el.dataset.progs, v ); },
		pub_q: text,
		pub_type: function ( el, v ) { return el.dataset.type === v; },
		pub_fac: function ( el, v ) { return has( el.dataset.fac, v ); },
		pub_year: function ( el, v, form ) {
			var y = parseInt( el.dataset.year, 10 );
			return 'earlier' === v ? y < parseInt( form.dataset.earlier, 10 ) : String( y ) === v;
		}
	};

	var lists = [
		{ box: '.ece-directory', item: '.ece-fcard' },
		{ box: '.ece-lab-list', item: '.ece-lcard' },
		{ box: '.ece-pubs', item: '.ece-cites > li' }
	];

	function values( form ) {
		var out = {};
		Array.prototype.forEach.call( form.elements, function ( f ) {
			if ( f.name && tests[ f.name ] && f.value.trim() ) {
				out[ f.name ] = f.value.trim();
			}
		} );
		return out;
	}

	function apply( box, form, item ) {
		var chosen = values( form );
		var shown = 0;
		box.querySelectorAll( '.ece-sec' ).forEach( function ( sec ) {
			var n = 0;
			sec.querySelectorAll( item ).forEach( function ( el ) {
				var ok = Object.keys( chosen ).every( function ( k ) {
					return tests[ k ]( el, chosen[ k ], form );
				} );
				el.hidden = ! ok;
				n += ok ? 1 : 0;
			} );
			sec.hidden = 0 === n;
			var count = sec.querySelector( '.ece-count' );
			if ( count ) {
				count.textContent = n;
			}
			shown += n;
		} );
		var empty = box.querySelector( '.ece-empty[data-js]' );
		if ( ! empty ) {
			empty = document.createElement( 'p' );
			empty.className = 'ece-empty';
			empty.setAttribute( 'data-js', '' );
			empty.setAttribute( 'role', 'status' );
			empty.textContent = 'Nothing matches these filters.';
			box.appendChild( empty );
		}
		empty.hidden = shown > 0;
		var bar = box.querySelector( '.ece-toolbar .ece-muted' );
		if ( bar ) {
			bar.textContent = shown + ( 1 === shown ? ' publication' : ' publications' ) + ', newest first';
		}
		return chosen;
	}

	function remember( chosen ) {
		var params = new URLSearchParams( window.location.search );
		Object.keys( tests ).forEach( function ( k ) {
			params.delete( k );
		} );
		Object.keys( chosen ).forEach( function ( k ) {
			params.set( k, chosen[ k ] );
		} );
		var q = params.toString();
		window.history.replaceState( null, '', window.location.pathname + ( q ? '?' + q : '' ) + window.location.hash );
	}

	document.addEventListener( 'DOMContentLoaded', function () {
		lists.forEach( function ( def ) {
			document.querySelectorAll( def.box + '[data-complete="1"]' ).forEach( function ( box ) {
				var form = box.querySelector( 'form.ece-filters' );
				if ( ! form ) {
					return;
				}
				// Choices already in the address (a shared link, or the static copy).
				var params = new URLSearchParams( window.location.search );
				Array.prototype.forEach.call( form.elements, function ( f ) {
					if ( f.name && tests[ f.name ] && params.has( f.name ) ) {
						f.value = params.get( f.name );
					}
				} );
				apply( box, form, def.item );
				form.addEventListener( 'submit', function ( e ) {
					e.preventDefault();
					remember( apply( box, form, def.item ) );
				} );
				form.addEventListener( 'change', function () {
					remember( apply( box, form, def.item ) );
				} );
				var timer;
				form.addEventListener( 'input', function () {
					clearTimeout( timer );
					timer = setTimeout( function () {
						remember( apply( box, form, def.item ) );
					}, 200 );
				} );
			} );
		} );
	} );
}() );
