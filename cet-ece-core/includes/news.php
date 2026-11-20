<?php
/**
 * News and announcements block: latest posts by category slug, as cards or a list.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

function cet_ece_render_news( $attributes ) {
	$limit    = ! empty( $attributes['limit'] ) ? (int) $attributes['limit'] : 3;
	$category = $attributes['category'] ?? '';
	$exclude  = $attributes['exclude'] ?? '';
	$style    = $attributes['style'] ?? 'cards';

	$args = array( 'post_type' => 'post', 'posts_per_page' => $limit, 'ignore_sticky_posts' => true, 'no_found_rows' => true );
	if ( $category ) {
		$args['category_name'] = $category;
	}
	if ( $exclude ) {
		$term = get_category_by_slug( $exclude );
		if ( $term ) {
			$args['category__not_in'] = array( $term->term_id );
		}
	}
	$posts = get_posts( $args );
	if ( ! $posts ) {
		return '<p class="ece-empty">Nothing posted yet.</p>';
	}

	$h = 'list' === $style ? '<ul class="ece-news-list">' : '<div class="ece-news-cards">';
	foreach ( $posts as $p ) {
		$cats  = get_the_category( $p->ID );
		$cat   = $cats ? $cats[0]->name : '';
		$meta  = trim( strtoupper( $cat ) . ' · ' . strtoupper( get_the_date( 'j M Y', $p ) ), ' ·' );
		$title = '<a href="' . esc_url( get_permalink( $p ) ) . '">' . esc_html( get_the_title( $p ) ) . '</a>';
		if ( 'list' === $style ) {
			$h .= '<li><span class="ece-news-meta">' . esc_html( $meta ) . '</span>' . $title . '</li>';
			continue;
		}
		$img = has_post_thumbnail( $p ) ? cet_ece_image( get_post_thumbnail_id( $p ), 'medium_large', get_the_title( $p ), 'ece-news-img' ) : '<span class="ece-news-img ece-ph" aria-hidden="true"></span>';
		$h  .= '<article class="ece-news-card">' . $img . '<div class="ece-news-body"><span class="ece-news-meta">' . esc_html( $meta ) . '</span><h3>' . $title . '</h3>';
		$ex  = get_the_excerpt( $p );
		if ( $ex ) {
			$h .= '<p>' . esc_html( wp_trim_words( $ex, 24 ) ) . '</p>';
		}
		$h .= '</div></article>';
	}
	return '<div class="ece-news">' . $h . ( 'list' === $style ? '</ul>' : '</div>' ) . '</div>';
}
