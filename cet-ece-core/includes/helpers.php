<?php
/**
 * Shared helpers.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

/**
 * Read a field. Uses the custom-fields plugin when present, raw meta otherwise,
 * so pages still render if the plugin is briefly deactivated.
 */
function cet_ece_get( $key, $post_id = null ) {
	$post_id = $post_id ? $post_id : get_the_ID();
	if ( function_exists( 'get_field' ) ) {
		return get_field( $key, $post_id );
	}
	return get_post_meta( $post_id, $key, true );
}

function cet_ece_designations() {
	return array(
		'professor'           => 'Professor',
		'associate_professor' => 'Associate Professor',
		'assistant_professor' => 'Assistant Professor',
	);
}

function cet_ece_designation_plural( $key ) {
	$map = array(
		'professor'           => 'Professors',
		'associate_professor' => 'Associate Professors',
		'assistant_professor' => 'Assistant Professors',
	);
	return $map[ $key ] ?? '';
}

/**
 * Programmes used by staff advisor batches: label, short label, duration in years.
 */
function cet_ece_programmes() {
	return array(
		'btech-ece' => array( 'B.Tech Electronics and Communication Engineering', 'B.Tech ECE', 4 ),
		'btech-aei' => array( 'B.Tech Applied Electronics and Instrumentation', 'B.Tech AEI', 4 ),
		'mtech-aei' => array( 'M.Tech Applied Electronics and Instrumentation', 'M.Tech AEI', 2 ),
		'mtech-cs'  => array( 'M.Tech Communication Systems', 'M.Tech CS', 2 ),
		'mtech-sp'  => array( 'M.Tech Signal Processing', 'M.Tech SP', 2 ),
		'mtech-mne' => array( 'M.Tech Micro and Nano Electronics', 'M.Tech MNE', 2 ),
		'mtech-ra'  => array( 'M.Tech Robotics and Automation', 'M.Tech RA', 2 ),
	);
}

function cet_ece_staff_categories() {
	return array(
		'instructor_grade_1'  => array( 'Instructor Grade I', 'Instructors Grade I' ),
		'instructor_grade_2'  => array( 'Instructor Grade II', 'Instructors Grade II' ),
		'trade_instructor'    => array( 'Trade Instructor', 'Trade Instructors' ),
		'instrument_mechanic' => array( 'Instrument Mechanic', 'Instrument Mechanics' ),
		'tradesman'           => array( 'Tradesman', 'Tradesmen' ),
		'other'               => array( 'Technical staff', 'Other technical staff' ),
	);
}

/**
 * The academic year starts in July. Returns the starting calendar year.
 */
function cet_ece_academic_year() {
	$y = (int) wp_date( 'Y' );
	$m = (int) wp_date( 'n' );
	return $m >= 7 ? $y : $y - 1;
}

/**
 * Whether a batch is still studying.
 */
function cet_ece_batch_is_current( $programme, $admission_year ) {
	$progs = cet_ece_programmes();
	$dur   = isset( $progs[ $programme ] ) ? $progs[ $programme ][2] : 4;
	return ( (int) $admission_year + $dur ) > cet_ece_academic_year();
}

/**
 * A faculty member's name, linked to their profile.
 */
function cet_ece_faculty_link( $id ) {
	$id = is_object( $id ) ? $id->ID : (int) $id;
	if ( ! $id || 'faculty' !== get_post_type( $id ) ) {
		return '';
	}
	return '<a href="' . esc_url( get_permalink( $id ) ) . '">' . esc_html( get_the_title( $id ) ) . '</a>';
}

function cet_ece_ids( $value ) {
	if ( empty( $value ) ) {
		return array();
	}
	$value = is_array( $value ) ? $value : array( $value );
	return array_values( array_filter( array_map( function ( $v ) {
		return is_object( $v ) ? (int) $v->ID : (int) $v;
	}, $value ) ) );
}

function cet_ece_badge( $text, $strong = false ) {
	return '<span class="ece-badge' . ( $strong ? ' is-strong' : '' ) . '">' . esc_html( $text ) . '</span>';
}

/**
 * A simple table. Cells are trusted HTML built by this plugin; escape before passing.
 */
function cet_ece_table( $heads, $rows ) {
	if ( empty( $rows ) ) {
		return '';
	}
	// tabindex and a label let keyboard users scroll a wide table on a phone.
	$h = '<div class="ece-table" role="region" tabindex="0" aria-label="' . esc_attr( implode( ', ', $heads ) ) . ' (scrollable table)"><table><thead><tr>';
	foreach ( $heads as $head ) {
		$h .= '<th scope="col">' . esc_html( $head ) . '</th>';
	}
	$h .= '</tr></thead><tbody>';
	foreach ( $rows as $row ) {
		$h .= '<tr>';
		foreach ( $row as $cell ) {
			$h .= '<td>' . $cell . '</td>';
		}
		$h .= '</tr>';
	}
	return $h . '</tbody></table></div>';
}

/**
 * An image from an attachment ID, with alt text falling back to a given label.
 */
function cet_ece_image( $attachment_id, $size, $fallback_alt, $class = '' ) {
	$attachment_id = is_array( $attachment_id ) ? (int) ( $attachment_id['ID'] ?? 0 ) : (int) $attachment_id;
	if ( ! $attachment_id ) {
		return '';
	}
	$alt = trim( (string) get_post_meta( $attachment_id, '_wp_attachment_image_alt', true ) );
	return wp_get_attachment_image( $attachment_id, $size, false, array(
		'class'   => $class,
		'alt'     => $alt ? $alt : $fallback_alt,
		'loading' => 'lazy',
	) );
}

/**
 * Format a publication as an IEEE-style citation.
 */
function cet_ece_cite( $pub_id ) {
	$authors = trim( (string) cet_ece_get( 'authors', $pub_id ) );
	$venue   = trim( (string) cet_ece_get( 'venue', $pub_id ) );
	$volume  = trim( (string) cet_ece_get( 'volume', $pub_id ) );
	$pages   = trim( (string) cet_ece_get( 'pages', $pub_id ) );
	$year    = trim( (string) cet_ece_get( 'year', $pub_id ) );
	$doi     = trim( (string) cet_ece_get( 'doi', $pub_id ) );
	$url     = trim( (string) cet_ece_get( 'url', $pub_id ) );
	$status  = cet_ece_get( 'status', $pub_id );

	$parts = array();
	if ( $authors ) {
		$parts[] = esc_html( $authors );
	}
	$parts[] = '&ldquo;' . esc_html( get_the_title( $pub_id ) ) . ',&rdquo;';
	if ( $venue ) {
		$parts[] = '<i>' . esc_html( $venue ) . '</i>';
	}
	if ( $volume ) {
		$parts[] = 'vol. ' . esc_html( $volume );
	}
	if ( $pages ) {
		$parts[] = 'pp. ' . esc_html( $pages );
	}
	if ( $year ) {
		$parts[] = esc_html( $year );
	}
	$out = implode( ', ', $parts );
	$out = str_replace( ',&rdquo;, ', ',&rdquo; ', $out ) . '.';
	if ( 'accepted' === $status ) {
		$out .= ' (Accepted.)';
	}
	if ( $doi ) {
		$out .= ' <a href="' . esc_url( 'https://doi.org/' . $doi ) . '">doi:' . esc_html( $doi ) . '</a>';
	} elseif ( $url ) {
		$out .= ' <a href="' . esc_url( $url ) . '">Link</a>';
	}
	return $out;
}

function cet_ece_pub_types() {
	return array(
		'journal'    => 'Journal',
		'conference' => 'Conference',
		'chapter'    => 'Book chapter',
		'patent'     => 'Patent',
		'other'      => 'Other',
	);
}
