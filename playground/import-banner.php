<?php
/**
 * Plugin Name: Import test site: keep out of search engines
 * Description: Keeps the Playground import test site out of search engines.
 */

// Keep the test site out of search engines.
add_filter( 'wp_robots', function ( $robots ) {
	$robots['noindex'] = true;
	$robots['nofollow'] = true;
	return $robots;
} );
