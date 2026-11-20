<?php
/**
 * Plugin Name: Import test banner
 * Description: Marks the Playground import site as a temporary copy.
 */

add_action( 'wp_body_open', function () {
	echo '<div style="background:#FFF4CC;color:#3D2E00;font:600 14px/1.4 system-ui,sans-serif;padding:10px 24px;text-align:center;border-bottom:1px solid #E6CF7A">Temporary test site for checking imported content. It lives only in this browser tab and is not the department website.</div>';
} );

// Keep the test site out of search engines.
add_filter( 'wp_robots', function ( $robots ) {
	$robots['noindex'] = true;
	$robots['nofollow'] = true;
	return $robots;
} );
