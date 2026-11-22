<?php
/**
 * Plugin Name: Demo banner
 * Description: Marks the Playground demo as a preview, so nobody mistakes it for the department's live website.
 */

add_action( 'wp_body_open', function () {
	echo '<div style="background:#FFF4CC;color:#3D2E00;font:600 14px/1.4 system-ui,sans-serif;padding:10px 24px;text-align:center;border-bottom:1px solid #E6CF7A">Preview of the new website. The content is copied from the current department website, ece.cet.ac.in, and has not been reviewed yet.</div>';
} );

// Keep the demo out of search engines.
add_filter( 'wp_robots', function ( $robots ) {
	$robots['noindex'] = true;
	$robots['nofollow'] = true;
	return $robots;
} );
