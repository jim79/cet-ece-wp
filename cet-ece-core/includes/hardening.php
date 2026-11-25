<?php
/**
 * Low-maintenance defaults: automatic updates, fewer attack surfaces,
 * no comments, sensible image handling.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

// No theme or plugin code editor in the admin.
if ( ! defined( 'DISALLOW_FILE_EDIT' ) ) {
	define( 'DISALLOW_FILE_EDIT', true );
}

// Automatic updates for WordPress, plugins and themes.
add_filter( 'allow_major_auto_core_updates', '__return_true' );
add_filter( 'auto_update_plugin', '__return_true' );
add_filter( 'auto_update_theme', '__return_true' );

// Do not advertise the WordPress version.
remove_action( 'wp_head', 'wp_generator' );
add_filter( 'the_generator', '__return_empty_string' );

// XML-RPC is not used by this site.
add_filter( 'xmlrpc_enabled', '__return_false' );

// Stop ?author=N from revealing user names.
add_action( 'template_redirect', function () {
	if ( is_author() || isset( $_GET['author'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		wp_safe_redirect( home_url( '/' ), 301 );
		exit;
	}
} );
add_filter( 'rest_endpoints', function ( $endpoints ) {
	if ( ! is_user_logged_in() ) {
		unset( $endpoints['/wp/v2/users'], $endpoints['/wp/v2/users/(?P<id>[\d]+)'] );
	}
	return $endpoints;
} );

// Comments are off everywhere: a department site does not need them and they attract spam.
add_action( 'init', function () {
	foreach ( get_post_types() as $type ) {
		if ( post_type_supports( $type, 'comments' ) ) {
			remove_post_type_support( $type, 'comments' );
			remove_post_type_support( $type, 'trackbacks' );
		}
	}
}, 100 );
add_filter( 'comments_open', '__return_false', 20 );
add_filter( 'pings_open', '__return_false', 20 );
add_filter( 'comments_array', '__return_empty_array', 10 );
add_action( 'admin_menu', function () {
	remove_menu_page( 'edit-comments.php' );
} );
add_action( 'wp_before_admin_bar_render', function () {
	global $wp_admin_bar;
	$wp_admin_bar->remove_menu( 'comments' );
} );

// Images: cap the largest stored size and save JPEG/PNG uploads as WebP where the server supports it.
add_filter( 'big_image_size_threshold', function () {
	return 2000;
} );
add_filter( 'image_editor_output_format', function ( $formats ) {
	if ( function_exists( 'wp_image_editor_supports' ) && wp_image_editor_supports( array( 'mime_type' => 'image/webp' ) ) ) {
		$formats['image/jpeg'] = 'image/webp';
		$formats['image/png']  = 'image/webp';
	}
	return $formats;
} );

// No emoji script: modern devices draw emoji themselves, and the script calls out to another server.
remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
remove_action( 'wp_print_styles', 'print_emoji_styles' );
remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
remove_action( 'admin_print_styles', 'print_emoji_styles' );
remove_filter( 'the_content_feed', 'wp_staticize_emoji' );
remove_filter( 'wp_mail', 'wp_staticize_emoji_for_email' );

// Tables added in the editor: make their scroll area reachable by keyboard on phones.
add_filter( 'render_block_core/table', function ( $html ) {
	if ( false === strpos( $html, 'tabindex=' ) ) {
		$html = preg_replace( '/<figure class="wp-block-table/', '<figure tabindex="0" role="region" aria-label="Table (scrollable)" class="wp-block-table', $html, 1 );
	}
	return $html;
} );
