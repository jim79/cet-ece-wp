<?php
/**
 * Content for the WordPress Playground demo: the department's real content,
 * converted from ece.cet.ac.in (playground/data/, made by tools/make_demo_data.py)
 * and loaded with the same importer as Tools > ECE import.
 *
 * To load quickly in a browser, the demo copies only profile photos, lab photos
 * and news images into the media library; PDFs and pictures inside posts stay
 * linked to the old site.
 */

if ( ! function_exists( 'update_field' ) ) {
	echo 'Secure Custom Fields is not active.';
	return;
}
if ( ! class_exists( 'CET_ECE_Importer' ) ) {
	echo 'The CET ECE Core plugin is not active.';
	return;
}

// Pages, homepage, categories, research areas.
if ( function_exists( 'cet_ece_create_starter_content' ) ) {
	cet_ece_create_starter_content();
}
if ( function_exists( 'cet_ece_seed_terms' ) ) {
	cet_ece_seed_terms();
}

// Remove WordPress's default sample content.
foreach ( array( 'hello-world' => 'post', 'sample-page' => 'page' ) as $slug => $type ) {
	$p = get_page_by_path( $slug, OBJECT, $type );
	if ( $p ) {
		wp_delete_post( $p->ID, true );
	}
}

// Only the image sizes the theme shows: fewer resized copies to make in the browser.
add_filter( 'intermediate_image_sizes_advanced', function ( $sizes ) {
	return array_intersect_key( $sizes, array_flip( array( 'thumbnail', 'medium_large', 'large' ) ) );
} );

$dir = __DIR__ . '/demo-data/';
foreach ( array( 'faculty', 'staff', 'labs', 'batches', 'publications', 'news', 'sections' ) as $type ) {
	$file = $dir . $type . '.csv';
	if ( ! is_readable( $file ) ) {
		echo "Missing $type.csv\n";
		continue;
	}
	$importer              = new CET_ECE_Importer();
	$importer->copy_linked = false;
	try {
		$log = $importer->run( $type, $file, false, true );
		echo $type . ': ' . count( $log ) . " rows\n";
	} catch ( Exception $e ) {
		echo $type . ': ' . $e->getMessage() . "\n";
	}
}

flush_rewrite_rules();
echo 'Demo content ready.';
