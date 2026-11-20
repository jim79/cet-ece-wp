/**
 * Editor side of the ECE blocks. Plain JavaScript, no build step.
 * Each block shows a live server-rendered preview and a few settings.
 */
( function ( wp ) {
	var el = wp.element.createElement;
	var registerBlockType = wp.blocks.registerBlockType;
	var SSR = wp.serverSideRender;
	var be = wp.blockEditor;
	var c = wp.components;

	function preview( name ) {
		return function ( props ) {
			var controls = [];
			var a = props.attributes;
			var set = props.setAttributes;
			if ( a.showFilters !== undefined ) {
				controls.push( el( c.ToggleControl, { key: 'f', label: 'Show filters', checked: !! a.showFilters, onChange: function ( v ) { set( { showFilters: v } ); } } ) );
			}
			if ( name === 'lab-list' ) {
				controls.push( el( c.SelectControl, { key: 't', label: 'Labs to show', value: a.type, options: [ { label: 'All labs', value: '' }, { label: 'Teaching labs', value: 'teaching' }, { label: 'Research labs', value: 'research' } ], onChange: function ( v ) { set( { type: v } ); } } ) );
			}
			if ( name === 'lab-list' ) {
				controls.push( el( c.TextControl, { key: 'p', label: 'Programme (slug)', help: 'btech-ece, btech-aei, mtech or phd. Leave empty for all.', value: a.programme, onChange: function ( v ) { set( { programme: v } ); } } ) );
			}
			if ( name === 'news' ) {
				controls.push( el( c.RangeControl, { key: 'n', label: 'Number of posts', value: a.limit, min: 1, max: 12, onChange: function ( v ) { set( { limit: v } ); } } ) );
				controls.push( el( c.TextControl, { key: 'c', label: 'Only this category (slug)', help: 'e.g. announcements. Leave empty for all.', value: a.category, onChange: function ( v ) { set( { category: v } ); } } ) );
				controls.push( el( c.TextControl, { key: 'x', label: 'Leave out this category (slug)', value: a.exclude, onChange: function ( v ) { set( { exclude: v } ); } } ) );
				controls.push( el( c.SelectControl, { key: 'y', label: 'Layout', value: a.style, options: [ { label: 'Cards with photos', value: 'cards' }, { label: 'Simple list', value: 'list' } ], onChange: function ( v ) { set( { style: v } ); } } ) );
			}
			if ( name === 'staff-advisors' ) {
				controls.push( el( c.SelectControl, { key: 's', label: 'Batches', value: a.type, options: [ { label: 'Current batches', value: 'current' }, { label: 'Past batches', value: 'past' } ], onChange: function ( v ) { set( { type: v } ); } } ) );
			}
			if ( name === 'publications' ) {
				controls.push( el( c.RangeControl, { key: 'l', label: 'Number to show (0 = all)', value: a.limit, min: 0, max: 50, onChange: function ( v ) { set( { limit: v } ); } } ) );
			}
			return el( 'div', be.useBlockProps(),
				controls.length ? el( be.InspectorControls, null, el( c.PanelBody, { title: 'Settings' }, controls ) ) : null,
				el( c.Disabled, null, el( SSR, { block: 'cet-ece/' + name, attributes: a, urlQueryArgs: props.context && props.context.postId ? { post_id: props.context.postId } : {} } ) )
			);
		};
	}

	var defs = {
		'copyright': [ 'Copyright line', 'editor-code' ],
		'last-updated': [ 'Page last updated', 'clock' ],
		'faculty-directory': [ 'Faculty directory', 'groups' ],
		'faculty-details': [ 'Faculty profile details', 'id' ],
		'lab-list': [ 'Lab list', 'admin-tools' ],
		'lab-details': [ 'Lab details', 'admin-tools' ],
		'projects': [ 'Funded projects', 'portfolio' ],
		'staff-advisors': [ 'Staff advisors', 'groups' ],
		'publications': [ 'Publications list', 'book' ],
		'research-areas': [ 'Research areas', 'tag' ],
		'tech-staff': [ 'Technical staff list', 'hammer' ],
		'news': [ 'News and announcements', 'megaphone' ]
	};

	Object.keys( defs ).forEach( function ( name ) {
		registerBlockType( 'cet-ece/' + name, {
			apiVersion: 3,
			title: defs[ name ][ 0 ],
			icon: defs[ name ][ 1 ],
			category: 'cet-ece',
			usesContext: [ 'postId', 'postType' ],
			edit: preview( name ),
			save: function () { return null; }
		} );
	} );
} )( window.wp );
