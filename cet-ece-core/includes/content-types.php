<?php
/**
 * Content types and taxonomies.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

function cet_ece_labels( $singular, $plural ) {
	return array(
		'name'               => $plural,
		'singular_name'      => $singular,
		'add_new'            => 'Add ' . strtolower( $singular ),
		'add_new_item'       => 'Add ' . strtolower( $singular ),
		'edit_item'          => 'Edit ' . strtolower( $singular ),
		'new_item'           => 'New ' . strtolower( $singular ),
		'view_item'          => 'View ' . strtolower( $singular ),
		'search_items'       => 'Search ' . strtolower( $plural ),
		'not_found'          => 'No ' . strtolower( $plural ) . ' found',
		'not_found_in_trash' => 'No ' . strtolower( $plural ) . ' in the bin',
		'all_items'          => 'All ' . strtolower( $plural ),
		'menu_name'          => $plural,
	);
}

function cet_ece_register_content_types() {
	register_post_type( 'faculty', array(
		'labels'        => cet_ece_labels( 'Faculty member', 'Faculty' ),
		'public'        => true,
		'show_in_rest'  => true,
		'has_archive'   => 'faculty',
		'rewrite'       => array( 'slug' => 'faculty', 'with_front' => false ),
		'menu_icon'     => 'dashicons-id',
		'menu_position' => 20,
		'supports'      => array( 'title', 'editor', 'revisions' ),
		'template'      => array( array( 'core/paragraph', array( 'placeholder' => 'About: two or three sentences on research focus and teaching, in the third person.' ) ) ),
	) );

	register_post_type( 'lab', array(
		'labels'        => cet_ece_labels( 'Lab', 'Labs' ),
		'public'        => true,
		'show_in_rest'  => true,
		'has_archive'   => 'labs',
		'rewrite'       => array( 'slug' => 'labs', 'with_front' => false ),
		'menu_icon'     => 'dashicons-admin-tools',
		'menu_position' => 21,
		'supports'      => array( 'title', 'editor', 'thumbnail', 'revisions' ),
		'template'      => array(
			array( 'core/paragraph', array( 'placeholder' => 'Describe the lab in a short paragraph. Add photos below with the Gallery block.' ) ),
			array( 'core/gallery', array() ),
		),
	) );

	register_post_type( 'batch', array(
		'labels'        => array_merge( cet_ece_labels( 'Batch', 'Staff advisors' ), array( 'add_new_item' => 'Add batch', 'all_items' => 'All batches' ) ),
		'public'        => false,
		'show_ui'       => true,
		'show_in_rest'  => true,
		'menu_icon'     => 'dashicons-groups',
		'menu_position' => 22,
		'supports'      => array( 'title' ),
	) );

	register_post_type( 'publication', array(
		'labels'        => cet_ece_labels( 'Publication', 'Publications' ),
		'public'        => false,
		'show_ui'       => true,
		'show_in_rest'  => true,
		'menu_icon'     => 'dashicons-book',
		'menu_position' => 23,
		'supports'      => array( 'title' ),
	) );

	register_post_type( 'staff', array(
		'labels'        => cet_ece_labels( 'Technical staff member', 'Technical staff' ),
		'public'        => false,
		'show_ui'       => true,
		'show_in_rest'  => true,
		'menu_icon'     => 'dashicons-hammer',
		'menu_position' => 24,
		'supports'      => array( 'title' ),
	) );

	register_taxonomy( 'research_area', array( 'faculty', 'lab', 'publication' ), array(
		'labels'            => cet_ece_labels( 'Research area', 'Research areas' ),
		'public'            => true,
		'hierarchical'      => false,
		'show_in_rest'      => true,
		'show_admin_column' => true,
		'rewrite'           => array( 'slug' => 'research-area', 'with_front' => false ),
	) );

	register_taxonomy( 'programme', array( 'lab' ), array(
		'labels'            => cet_ece_labels( 'Programme', 'Programmes' ),
		'public'            => false,
		'show_ui'           => true,
		'hierarchical'      => true,
		'show_in_rest'      => true,
		'show_admin_column' => true,
	) );
}
add_action( 'init', 'cet_ece_register_content_types' );

/**
 * Starting terms. Safe to run more than once.
 */
function cet_ece_seed_terms() {
	$progs = array(
		'btech-ece' => 'B.Tech ECE',
		'btech-aei' => 'B.Tech AEI',
		'mtech'     => 'M.Tech',
		'phd'       => 'Ph.D.',
	);
	foreach ( $progs as $slug => $name ) {
		if ( ! term_exists( $slug, 'programme' ) ) {
			wp_insert_term( $name, 'programme', array( 'slug' => $slug ) );
		}
	}
	$areas = array(
		'Signal and image processing',
		'Communication systems',
		'Optics and photonics',
		'Biomedical engineering',
		'Control and power electronics',
		'Machine learning',
		'VLSI and micro-nano electronics',
	);
	foreach ( $areas as $name ) {
		if ( ! term_exists( $name, 'research_area' ) ) {
			wp_insert_term( $name, 'research_area' );
		}
	}
}

/**
 * Admin list columns that help editors scan entries.
 */
add_filter( 'manage_faculty_posts_columns', function ( $cols ) {
	$cols['designation'] = 'Designation';
	return $cols;
} );
add_action( 'manage_faculty_posts_custom_column', function ( $col, $id ) {
	if ( 'designation' === $col ) {
		$d = cet_ece_designations();
		echo esc_html( $d[ cet_ece_get( 'designation', $id ) ] ?? '' );
	}
}, 10, 2 );

add_filter( 'manage_batch_posts_columns', function ( $cols ) {
	$cols['status'] = 'Status';
	return $cols;
} );
add_action( 'manage_batch_posts_custom_column', function ( $col, $id ) {
	if ( 'status' === $col ) {
		echo cet_ece_batch_is_current( cet_ece_get( 'programme', $id ), cet_ece_get( 'admission_year', $id ) ) ? 'Current' : 'Graduated';
	}
}, 10, 2 );

/**
 * One-time repair: sites set up by earlier versions of the theme saved address
 * rules for the wrong permalink structure, so news posts led to the homepage.
 * Rebuild them once, after content types are registered.
 */
add_action( 'init', function () {
	if ( get_option( 'cet_ece_rules_v2' ) ) {
		return;
	}
	global $wp_rewrite;
	$structure = (string) get_option( 'permalink_structure' );
	if ( '' !== $structure ) {
		$wp_rewrite->set_permalink_structure( $structure );
		flush_rewrite_rules();
	}
	update_option( 'cet_ece_rules_v2', 1 );
}, 99 );
