<?php
/**
 * Form rules that keep content consistent.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

// Institutional email only.
add_filter( 'acf/validate_value/key=field_ece_fac_email', function ( $valid, $value ) {
	if ( true !== $valid || '' === $value ) {
		return $valid;
	}
	return preg_match( '/@cet\.ac\.in$/i', trim( $value ) ) ? true : 'Use an institutional address ending in @cet.ac.in.';
}, 10, 2 );

// Photo must carry alt text.
add_filter( 'acf/validate_value/key=field_ece_fac_photo', function ( $valid, $value ) {
	if ( true !== $valid || empty( $value ) ) {
		return $valid;
	}
	$alt = trim( (string) get_post_meta( (int) $value, '_wp_attachment_image_alt', true ) );
	return '' !== $alt ? true : 'Add alternative text to the photo: open it in the media window and fill in "Alternative text".';
}, 10, 2 );

// DOI: accept a bare DOI or a doi.org link, store the bare DOI.
add_filter( 'acf/update_value/key=field_ece_pub_doi', function ( $value ) {
	$value = trim( (string) $value );
	return preg_replace( '#^(https?://)?(dx\.)?doi\.org/#i', '', $value );
} );
add_filter( 'acf/validate_value/key=field_ece_pub_doi', function ( $valid, $value ) {
	if ( true !== $valid || '' === trim( (string) $value ) ) {
		return $valid;
	}
	$doi = preg_replace( '#^(https?://)?(dx\.)?doi\.org/#i', '', trim( $value ) );
	return preg_match( '#^10\.\d{4,9}/\S+$#', $doi ) ? true : 'A DOI starts with "10." followed by a slash, e.g. 10.1109/ACCESS.2025.1234567.';
}, 10, 2 );

// Batch titles are generated, e.g. "B.Tech ECE 2026 A".
add_action( 'acf/save_post', function ( $post_id ) {
	if ( 'batch' !== get_post_type( $post_id ) ) {
		return;
	}
	$progs = cet_ece_programmes();
	$prog  = cet_ece_get( 'programme', $post_id );
	$title = trim( ( $progs[ $prog ][1] ?? 'Batch' ) . ' ' . cet_ece_get( 'admission_year', $post_id ) . ' ' . cet_ece_get( 'batch_label', $post_id ) );
	if ( get_the_title( $post_id ) !== $title ) {
		wp_update_post( array( 'ID' => $post_id, 'post_title' => $title, 'post_name' => sanitize_title( $title ) ) );
	}
}, 20 );

add_filter( 'enter_title_here', function ( $text, $post ) {
	$map = array(
		'faculty'     => 'Full name, e.g. Dr. A. Name',
		'lab'         => 'Lab name',
		'publication' => 'Paper title',
		'staff'       => 'Full name',
		'batch'       => 'Filled in automatically on save',
	);
	return $map[ $post->post_type ] ?? $text;
}, 10, 2 );
