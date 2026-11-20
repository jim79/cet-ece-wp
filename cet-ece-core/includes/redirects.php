<?php
/**
 * Permanent redirects from the old site's addresses, so existing links and
 * search results keep working. Applied only when the old address would 404.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

function cet_ece_old_urls() {
	return array(
		'faculty-2'                   => '/faculty/',
		'placements-latest'           => '/placements/',
		'research-overview'           => '/research/',
		'publications'                => '/research/publications/',
		'activities'                  => '/news/',
		'laboratories'                => '/labs/',
		'golden-jubilee-celebrations' => '/about/',
		'obe'                         => '/academics/obe/',
		'programs'                    => '/academics/',
		'staff-advisors'              => '/staff-advisors/',
		'technical-staff'             => '/technical-staff/',
	);
}

add_action( 'template_redirect', function () {
	if ( ! is_404() ) {
		return;
	}
	$path = trim( (string) wp_parse_url( $_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH ), '/' ); // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
	$map  = cet_ece_old_urls();
	if ( isset( $map[ $path ] ) && trailingslashit( '/' . $path ) !== $map[ $path ] ) {
		wp_safe_redirect( home_url( $map[ $path ] ), 301 );
		exit;
	}
} );
