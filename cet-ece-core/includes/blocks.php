<?php
/**
 * Block registration. All blocks are rendered on the server; the editor shows
 * a live preview through ServerSideRender, so there is no build step.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

function cet_ece_block_defs() {
	return array(
		'copyright'         => array( 'cet_ece_render_copyright', array() ),
		'last-updated'      => array( 'cet_ece_render_last_updated', array() ),
		'faculty-directory' => array( 'cet_ece_render_faculty_directory', array( 'showFilters' => array( 'type' => 'boolean', 'default' => true ), 'area' => array( 'type' => 'string', 'default' => '' ) ) ),
		'faculty-details'   => array( 'cet_ece_render_faculty_details', array() ),
		'lab-list'          => array( 'cet_ece_render_lab_list', array( 'type' => array( 'type' => 'string', 'default' => '' ), 'programme' => array( 'type' => 'string', 'default' => '' ), 'showFilters' => array( 'type' => 'boolean', 'default' => false ) ) ),
		'lab-details'       => array( 'cet_ece_render_lab_details', array() ),
		'projects'          => array( 'cet_ece_render_projects', array() ),
		'staff-advisors'    => array( 'cet_ece_render_staff_advisors', array( 'type' => array( 'type' => 'string', 'default' => 'current' ) ) ),
		'publications'      => array( 'cet_ece_render_publications', array( 'showFilters' => array( 'type' => 'boolean', 'default' => true ), 'limit' => array( 'type' => 'number', 'default' => 0 ) ) ),
		'research-areas'    => array( 'cet_ece_render_research_areas', array() ),
		'tech-staff'        => array( 'cet_ece_render_tech_staff', array() ),
		'news'              => array( 'cet_ece_render_news', array( 'limit' => array( 'type' => 'number', 'default' => 3 ), 'category' => array( 'type' => 'string', 'default' => '' ), 'exclude' => array( 'type' => 'string', 'default' => '' ), 'style' => array( 'type' => 'string', 'default' => 'cards' ) ) ),
	);
}

add_action( 'init', function () {
	wp_register_style( 'cet-ece-blocks', CET_ECE_CORE_URL . 'assets/blocks.css', array(), CET_ECE_CORE_VERSION );
	wp_register_script(
		'cet-ece-blocks-editor',
		CET_ECE_CORE_URL . 'assets/editor.js',
		array( 'wp-blocks', 'wp-element', 'wp-server-side-render', 'wp-block-editor', 'wp-components' ),
		CET_ECE_CORE_VERSION,
		true
	);
	foreach ( cet_ece_block_defs() as $name => $def ) {
		register_block_type( 'cet-ece/' . $name, array(
			'api_version'     => 3,
			'title'           => ucwords( str_replace( '-', ' ', $name ) ),
			'category'        => 'cet-ece',
			'attributes'      => $def[1],
			'uses_context'    => array( 'postId', 'postType' ),
			'render_callback' => $def[0],
			'editor_script'   => 'cet-ece-blocks-editor',
			'style'           => 'cet-ece-blocks',
			'supports'        => array( 'html' => false, 'align' => array( 'wide', 'full' ) ),
		) );
	}
} );

add_filter( 'block_categories_all', function ( $cats ) {
	array_unshift( $cats, array( 'slug' => 'cet-ece', 'title' => 'ECE department' ) );
	return $cats;
} );
