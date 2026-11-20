<?php
/**
 * BibTeX export for the publications list: add ?ece_bibtex=1 to the page URL.
 * The current filters apply.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

add_action( 'template_redirect', function () {
	if ( empty( $_GET['ece_bibtex'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		return;
	}
	list( $ids ) = cet_ece_publication_query( array( 'showFilters' => true ) );
	$map         = array( 'journal' => 'article', 'conference' => 'inproceedings', 'chapter' => 'incollection', 'patent' => 'misc', 'other' => 'misc' );
	$out         = '';
	foreach ( $ids as $id ) {
		$type  = $map[ cet_ece_get( 'pub_type', $id ) ] ?? 'misc';
		$year  = (string) cet_ece_get( 'year', $id );
		$lead  = preg_split( '/,|\s+and\s+/', (string) cet_ece_get( 'authors', $id ) );
		$words = preg_split( '/\s+/', trim( (string) ( $lead[0] ?? '' ) ) );
		$first = strtolower( preg_replace( '/[^A-Za-z]/', '', (string) end( $words ) ) );
		$key   = ( $first ? substr( $first, -12 ) : 'ece' ) . $year . '_' . $id;
		$venue = 'article' === $type ? 'journal' : 'booktitle';
		$f     = array(
			'title'  => get_the_title( $id ),
			'author' => str_replace( array( ', and ', ',' ), array( ' and ', ' and' ), (string) cet_ece_get( 'authors', $id ) ),
			$venue   => cet_ece_get( 'venue', $id ),
			'volume' => cet_ece_get( 'volume', $id ),
			'pages'  => cet_ece_get( 'pages', $id ),
			'year'   => $year,
			'doi'    => cet_ece_get( 'doi', $id ),
			'url'    => cet_ece_get( 'url', $id ),
		);
		$out  .= '@' . $type . '{' . $key . ",\n";
		foreach ( $f as $k => $v ) {
			$v = trim( (string) $v );
			if ( '' !== $v ) {
				$out .= '  ' . $k . ' = {' . str_replace( array( '{', '}' ), '', $v ) . "},\n";
			}
		}
		$out .= "}\n\n";
	}
	nocache_headers();
	header( 'Content-Type: application/x-bibtex; charset=utf-8' );
	header( 'Content-Disposition: attachment; filename="ece-cet-publications.bib"' );
	echo $out; // phpcs:ignore WordPress.Security.EscapeOutput
	exit;
} );
