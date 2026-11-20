<?php
/**
 * Plugin Name: Demo banner
 * Description: Marks the Playground demo so nobody mistakes sample content for real data.
 */

add_action( 'wp_body_open', function () {
	echo '<div style="background:#FFF4CC;color:#3D2E00;font:600 14px/1.4 system-ui,sans-serif;padding:10px 24px;text-align:center;border-bottom:1px solid #E6CF7A">Demo site with sample content. Faculty names, publications, projects and figures are invented. News items are from the current department website.</div>';
} );

// Keep the demo out of search engines.
add_filter( 'wp_robots', function ( $robots ) {
	$robots['noindex'] = true;
	$robots['nofollow'] = true;
	return $robots;
} );
