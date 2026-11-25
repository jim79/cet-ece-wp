<?php
/**
 * Plugin Name: Demo: keep out of search engines
 * Description: The Playground demo and the GitHub Pages copy are previews of the department website. They stay out of search results so they never compete with the real site.
 */

add_filter( 'wp_robots', function ( $robots ) {
	$robots['noindex'] = true;
	$robots['nofollow'] = true;
	return $robots;
} );
