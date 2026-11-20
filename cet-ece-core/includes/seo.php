<?php
/**
 * Search and sharing basics: a meta description, Open Graph tags (the preview
 * card in WhatsApp, Facebook and LinkedIn) and organisation data on the homepage.
 * Steps aside if an SEO plugin is installed.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

function cet_ece_seo_plugin_active() {
	return defined( 'WPSEO_VERSION' ) || class_exists( 'RankMath' ) || defined( 'AIOSEO_VERSION' ) || defined( 'SEOPRESS_VERSION' );
}

function cet_ece_page_description() {
	if ( is_front_page() ) {
		return 'Department of Electronics and Communication Engineering, College of Engineering Trivandrum: B.Tech, M.Tech and Ph.D. programmes, faculty, labs, research and placements.';
	}
	if ( is_singular() ) {
		$id   = get_queried_object_id();
		$type = get_post_type( $id );
		if ( 'faculty' === $type ) {
			$d     = cet_ece_designations();
			$areas = get_the_terms( $id, 'research_area' );
			$text  = get_the_title( $id ) . ', ' . ( $d[ cet_ece_get( 'designation', $id ) ] ?? 'Faculty' ) . ', Department of ECE, College of Engineering Trivandrum.';
			if ( $areas && ! is_wp_error( $areas ) ) {
				$text .= ' Research: ' . implode( ', ', wp_list_pluck( $areas, 'name' ) ) . '.';
			}
			return $text;
		}
		if ( 'lab' === $type && cet_ece_get( 'summary', $id ) ) {
			return cet_ece_get( 'summary', $id );
		}
		$excerpt = get_post_field( 'post_excerpt', $id );
		if ( ! $excerpt ) {
			$excerpt = wp_trim_words( wp_strip_all_tags( strip_shortcodes( get_post_field( 'post_content', $id ) ) ), 30, '…' );
		}
		return $excerpt;
	}
	if ( is_post_type_archive( 'faculty' ) ) {
		return 'Faculty of the Department of Electronics and Communication Engineering, College of Engineering Trivandrum.';
	}
	if ( is_post_type_archive( 'lab' ) ) {
		return 'Teaching and research laboratories of the Department of Electronics and Communication Engineering, College of Engineering Trivandrum.';
	}
	if ( is_category() || is_tax() ) {
		$d = term_description();
		return $d ? wp_strip_all_tags( $d ) : single_term_title( '', false ) . ' · Department of ECE, College of Engineering Trivandrum';
	}
	return get_bloginfo( 'description' );
}

function cet_ece_page_image() {
	if ( is_singular() ) {
		$id = get_queried_object_id();
		if ( 'faculty' === get_post_type( $id ) && cet_ece_get( 'photo', $id ) ) {
			return wp_get_attachment_image_url( (int) cet_ece_get( 'photo', $id ), 'large' );
		}
		if ( has_post_thumbnail( $id ) ) {
			return get_the_post_thumbnail_url( $id, 'large' );
		}
	}
	$logo = get_theme_mod( 'custom_logo' );
	if ( $logo ) {
		return wp_get_attachment_image_url( $logo, 'full' );
	}
	return get_site_icon_url( 512 );
}

add_action( 'wp_head', function () {
	if ( cet_ece_seo_plugin_active() || is_404() ) {
		return;
	}
	$desc  = trim( preg_replace( '/\s+/', ' ', (string) cet_ece_page_description() ) );
	$title = wp_get_document_title();
	$url   = is_singular() ? get_permalink() : home_url( add_query_arg( array() ) );
	$img   = cet_ece_page_image();

	if ( $desc ) {
		echo '<meta name="description" content="' . esc_attr( $desc ) . '">' . "\n";
	}
	echo '<meta property="og:site_name" content="' . esc_attr( get_bloginfo( 'name' ) ) . '">' . "\n";
	echo '<meta property="og:title" content="' . esc_attr( $title ) . '">' . "\n";
	echo '<meta property="og:type" content="' . ( is_singular( 'post' ) ? 'article' : 'website' ) . '">' . "\n";
	echo '<meta property="og:url" content="' . esc_url( $url ) . '">' . "\n";
	if ( $desc ) {
		echo '<meta property="og:description" content="' . esc_attr( $desc ) . '">' . "\n";
	}
	if ( $img ) {
		echo '<meta property="og:image" content="' . esc_url( $img ) . '">' . "\n";
	}
	echo '<meta name="twitter:card" content="' . ( $img ? 'summary_large_image' : 'summary' ) . '">' . "\n";

	if ( is_front_page() ) {
		$org = array(
			'@context'           => 'https://schema.org',
			'@type'              => 'EducationalOrganization',
			'name'               => 'Department of Electronics and Communication Engineering, College of Engineering Trivandrum',
			'url'                => home_url( '/' ),
			'email'              => 'hodece@cet.ac.in',
			'telephone'          => '+91-471-2515563',
			'foundingDate'       => '1964',
			'parentOrganization' => array( '@type' => 'CollegeOrUniversity', 'name' => 'College of Engineering Trivandrum', 'url' => 'https://www.cet.ac.in/' ),
			'address'            => array( '@type' => 'PostalAddress', 'addressLocality' => 'Thiruvananthapuram', 'addressRegion' => 'Kerala', 'addressCountry' => 'IN', 'streetAddress' => 'Sreekariyam' ),
		);
		if ( $img ) {
			$org['logo'] = $img;
		}
		echo '<script type="application/ld+json">' . wp_json_encode( $org, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) . '</script>' . "\n";
	}
}, 5 );
