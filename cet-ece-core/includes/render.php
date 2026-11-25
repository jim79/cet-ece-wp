<?php
/**
 * Server-side rendering for the plugin's blocks.
 * Every function returns escaped HTML.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

/* ---------- small pieces ---------- */

function cet_ece_crumbs( $items ) {
	$out = array();
	foreach ( $items as $item ) {
		$out[] = $item[1] ? '<a href="' . esc_url( $item[1] ) . '">' . esc_html( $item[0] ) . '</a>' : '<span aria-current="page">' . esc_html( $item[0] ) . '</span>';
	}
	return '<nav class="ece-crumbs" aria-label="Breadcrumb">' . implode( '<span aria-hidden="true">/</span>', $out ) . '</nav>';
}

function cet_ece_side_card( $title, $inner ) {
	return $inner ? '<div class="ece-side-card"><h2>' . esc_html( $title ) . '</h2>' . $inner . '</div>' : '';
}

function cet_ece_section( $title, $inner, $id = '' ) {
	if ( ! $inner ) {
		return '';
	}
	return '<section class="ece-sec"' . ( $id ? ' id="' . esc_attr( $id ) . '"' : '' ) . '><h2>' . esc_html( $title ) . '</h2>' . $inner . '</section>';
}

function cet_ece_facts( $pairs ) {
	$h = '';
	foreach ( $pairs as $k => $v ) {
		if ( '' !== (string) $v ) {
			$h .= '<div class="ece-fact"><span class="ece-fact-k">' . esc_html( $k ) . '</span><span class="ece-fact-v">' . $v . '</span></div>';
		}
	}
	return $h ? '<div class="ece-facts">' . $h . '</div>' : '';
}

function cet_ece_term_chips( $post_id, $tax = 'research_area' ) {
	$terms = get_the_terms( $post_id, $tax );
	if ( ! $terms || is_wp_error( $terms ) ) {
		return '';
	}
	$h = '<div class="ece-chips">';
	foreach ( $terms as $t ) {
		$link = 'research_area' === $tax ? get_term_link( $t ) : '';
		$h   .= $link && ! is_wp_error( $link ) ? '<a class="ece-chip" href="' . esc_url( $link ) . '">' . esc_html( $t->name ) . '</a>' : '<span class="ece-chip">' . esc_html( $t->name ) . '</span>';
	}
	return $h . '</div>';
}

function cet_ece_file_link( $file_id, $label ) {
	$file_id = (int) $file_id;
	return $file_id ? '<a href="' . esc_url( wp_get_attachment_url( $file_id ) ) . '">' . esc_html( $label ) . '</a>' : '';
}

function cet_ece_current_term() {
	if ( is_tax( 'research_area' ) ) {
		$t = get_queried_object();
		return $t ? $t->slug : '';
	}
	return '';
}

function cet_ece_get_param( $key ) {
	return isset( $_GET[ $key ] ) ? sanitize_text_field( wp_unslash( $_GET[ $key ] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification
}

/* ---------- copyright and last updated ---------- */

function cet_ece_render_copyright() {
	return '<p class="ece-copyright">&copy; ' . esc_html( wp_date( 'Y' ) ) . ' Department of Electronics and Communication Engineering, College of Engineering Trivandrum</p>';
}

function cet_ece_render_last_updated( $attributes, $content, $block ) {
	$id = $block->context['postId'] ?? get_queried_object_id();
	if ( ! $id ) {
		return '';
	}
	return '<p class="ece-updated">Page last updated: ' . esc_html( get_the_modified_date( 'j M Y', $id ) ) . '</p>';
}

/* ---------- faculty ---------- */

/** Space-separated term slugs, for the in-page filters (assets/filters.js). */
function cet_ece_term_slugs( $id, $tax ) {
	$terms = get_the_terms( $id, $tax );
	return $terms && ! is_wp_error( $terms ) ? implode( ' ', wp_list_pluck( $terms, 'slug' ) ) : '';
}

function cet_ece_faculty_card( $id ) {
	$d     = cet_ece_designations();
	$des   = $d[ cet_ece_get( 'designation', $id ) ] ?? '';
	$role  = cet_ece_get( 'additional_role', $id );
	$email = cet_ece_get( 'email', $id );
	$areas = get_the_terms( $id, 'research_area' );
	$names = $areas && ! is_wp_error( $areas ) ? implode( ', ', wp_list_pluck( array_slice( $areas, 0, 3 ), 'name' ) ) : '';
	$img   = cet_ece_image( cet_ece_get( 'photo', $id ), 'thumbnail', 'Photo of ' . get_the_title( $id ), 'ece-avatar' );
	if ( ! $img ) {
		$img = '<span class="ece-avatar ece-ph" aria-hidden="true"></span>';
	}
	$h  = '<article class="ece-fcard" data-des="' . esc_attr( cet_ece_get( 'designation', $id ) ) . '" data-areas="' . esc_attr( cet_ece_term_slugs( $id, 'research_area' ) ) . '">' . $img . '<div class="ece-fcard-body">';
	$h .= '<h3 class="ece-fcard-name"><a href="' . esc_url( get_permalink( $id ) ) . '">' . esc_html( get_the_title( $id ) ) . '</a></h3>';
	$h .= '<p class="ece-fcard-role">' . esc_html( $des ) . ( $role ? ' · ' . esc_html( $role ) : '' ) . '</p>';
	if ( $names ) {
		$h .= '<p class="ece-fcard-areas">' . esc_html( $names ) . '</p>';
	}
	if ( $email ) {
		$h .= '<p class="ece-fcard-email"><a href="mailto:' . esc_attr( antispambot( $email ) ) . '">' . esc_html( antispambot( $email ) ) . '</a></p>';
	}
	return $h . '</div></article>';
}

function cet_ece_sort_people( $ids ) {
	usort( $ids, function ( $a, $b ) {
		$oa = cet_ece_get( 'display_order', $a );
		$ob = cet_ece_get( 'display_order', $b );
		$oa = ( '' === $oa || null === $oa ) ? PHP_INT_MAX : (int) $oa;
		$ob = ( '' === $ob || null === $ob ) ? PHP_INT_MAX : (int) $ob;
		if ( $oa !== $ob ) {
			return $oa <=> $ob;
		}
		return strcasecmp( preg_replace( '/^(Dr\.|Prof\.)\s*/i', '', get_the_title( $a ) ), preg_replace( '/^(Dr\.|Prof\.)\s*/i', '', get_the_title( $b ) ) );
	} );
	return $ids;
}

function cet_ece_render_faculty_directory( $attributes ) {
	$show_filters = ! isset( $attributes['showFilters'] ) || $attributes['showFilters'];
	$area         = ! empty( $attributes['area'] ) ? $attributes['area'] : cet_ece_current_term();
	$q            = $show_filters ? cet_ece_get_param( 'f_q' ) : '';
	$des          = $show_filters ? cet_ece_get_param( 'f_des' ) : '';
	if ( $show_filters && cet_ece_get_param( 'f_area' ) ) {
		$area = cet_ece_get_param( 'f_area' );
	}

	$args = array( 'post_type' => 'faculty', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true );
	if ( $q ) {
		$args['s'] = $q;
	}
	if ( $area ) {
		$args['tax_query'] = array( array( 'taxonomy' => 'research_area', 'field' => 'slug', 'terms' => $area ) ); // phpcs:ignore WordPress.DB.SlowDBQuery
	}
	$ids = get_posts( $args );

	$groups = array();
	foreach ( array_keys( cet_ece_designations() ) as $k ) {
		$groups[ $k ] = array();
	}
	foreach ( $ids as $id ) {
		$k = cet_ece_get( 'designation', $id );
		if ( isset( $groups[ $k ] ) && ( ! $des || $des === $k ) ) {
			$groups[ $k ][] = $id;
		}
	}

	$complete = ! $q && ! $des && ( ! $area || ! empty( $attributes['area'] ) || is_tax() );
	$h        = '<div class="ece-directory" data-complete="' . ( $complete ? '1' : '0' ) . '">';
	if ( $show_filters && ! is_tax() ) {
		wp_enqueue_script( 'cet-ece-filters' );
		$h .= '<form class="ece-filters" method="get" role="search" aria-label="Filter faculty">';
		$h .= '<div class="ece-field ece-field-wide"><label for="f_q">Search by name or keyword</label><input id="f_q" name="f_q" type="search" value="' . esc_attr( $q ) . '"></div>';
		$h .= '<div class="ece-field"><label for="f_des">Designation</label><select id="f_des" name="f_des"><option value="">All designations</option>';
		foreach ( cet_ece_designations() as $k => $label ) {
			$h .= '<option value="' . esc_attr( $k ) . '"' . selected( $des, $k, false ) . '>' . esc_html( $label ) . '</option>';
		}
		$h .= '</select></div><div class="ece-field"><label for="f_area">Research area</label><select id="f_area" name="f_area"><option value="">All areas</option>';
		$terms = get_terms( array( 'taxonomy' => 'research_area', 'hide_empty' => false ) );
		if ( ! is_wp_error( $terms ) ) {
			foreach ( $terms as $t ) {
				$h .= '<option value="' . esc_attr( $t->slug ) . '"' . selected( $area, $t->slug, false ) . '>' . esc_html( $t->name ) . '</option>';
			}
		}
		$h .= '</select></div><div class="ece-field ece-field-btn"><button type="submit" class="wp-element-button">Show</button></div></form>';
	}

	$total = 0;
	if ( 'designation' !== ( $attributes['order'] ?? 'seniority' ) ) {
		// One list in order of service seniority (the Seniority order field), as on the department's notice board.
		$list = array();
		foreach ( $groups as $g ) {
			$list = array_merge( $list, $g );
		}
		if ( $list ) {
			$total = count( $list );
			$h    .= '<section class="ece-sec"><div class="ece-grid">';
			foreach ( cet_ece_sort_people( $list ) as $id ) {
				$h .= cet_ece_faculty_card( $id );
			}
			$h .= '</div></section>';
		}
		$groups = array();
	}
	foreach ( $groups as $k => $list ) {
		if ( ! $list ) {
			continue;
		}
		$total += count( $list );
		$h     .= '<section class="ece-sec"><h2>' . esc_html( cet_ece_designation_plural( $k ) ) . ' <span class="ece-count">' . count( $list ) . '</span></h2><div class="ece-grid">';
		foreach ( cet_ece_sort_people( $list ) as $id ) {
			$h .= cet_ece_faculty_card( $id );
		}
		$h .= '</div></section>';
	}
	if ( ! $total ) {
		$h .= '<p class="ece-empty">No faculty match these filters.</p>';
	}
	return $h . '</div>';
}

function cet_ece_faculty_labs( $id ) {
	return get_posts( array(
		'post_type'      => 'lab',
		'posts_per_page' => -1,
		'fields'         => 'ids',
		'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery
			'relation' => 'OR',
			array( 'key' => 'lead_faculty', 'value' => $id ),
			array( 'key' => 'members', 'value' => '"' . $id . '"', 'compare' => 'LIKE' ),
		),
	) );
}

function cet_ece_render_faculty_details( $attributes, $content, $block ) {
	$id = $block->context['postId'] ?? get_the_ID();
	if ( ! $id || 'faculty' !== get_post_type( $id ) ) {
		return '';
	}
	$name  = get_the_title( $id );
	$d     = cet_ece_designations();
	$des   = $d[ cet_ece_get( 'designation', $id ) ] ?? '';
	$role  = cet_ece_get( 'additional_role', $id );
	$email = cet_ece_get( 'email', $id );

	// Aside.
	$photo = cet_ece_image( cet_ece_get( 'photo', $id ), 'medium_large', 'Photo of ' . $name, 'ece-portrait' );
	$aside = $photo ? $photo : '<div class="ece-portrait ece-ph" aria-hidden="true"></div>';

	$contact = '';
	if ( $email ) {
		$contact .= '<a href="mailto:' . esc_attr( antispambot( $email ) ) . '">' . esc_html( antispambot( $email ) ) . '</a>';
	}
	if ( cet_ece_get( 'room', $id ) ) {
		$contact .= '<span>' . esc_html( cet_ece_get( 'room', $id ) ) . '</span>';
	}
	$contact .= '<span>Department office: 0471-2515563</span>';
	$aside   .= cet_ece_side_card( 'Contact', $contact );

	$profiles = '';
	foreach ( array( 'scholar_url' => 'Google Scholar', 'orcid_url' => 'ORCID', 'scopus_url' => 'Scopus' ) as $key => $label ) {
		$u = cet_ece_get( $key, $id );
		if ( $u ) {
			$profiles .= '<a class="ece-btn-outline" href="' . esc_url( $u ) . '">' . esc_html( $label ) . '</a>';
		}
	}
	if ( $profiles ) {
		$aside .= cet_ece_side_card( 'Research profiles', '<div class="ece-btn-row">' . $profiles . '</div>' );
	}

	// Main.
	$main  = '<div class="ece-profile-head"><h1>' . esc_html( $name ) . '</h1>';
	// The role comes last: "Principal" and "Dean" are college roles, not the department's.
	$main .= '<p class="ece-profile-role">' . esc_html( $des ) . ', Department of Electronics and Communication Engineering' . ( $role ? ' · ' . esc_html( $role ) : '' ) . '</p>';
	if ( cet_ece_get( 'joined_year', $id ) ) {
		$main .= '<p class="ece-muted">With the department since ' . esc_html( cet_ece_get( 'joined_year', $id ) ) . '</p>';
	}
	$main .= '</div>';

	$bio = trim( get_post_field( 'post_content', $id ) );
	if ( $bio ) {
		$main .= cet_ece_section( 'About', '<div class="ece-prose">' . apply_filters( 'the_content', $bio ) . '</div>' ); // phpcs:ignore WordPress.NamingConventions.PrefixAllGlobals
	}
	$main .= cet_ece_section( 'Research areas', cet_ece_term_chips( $id ) );

	$rows  = array();
	$quals = array_filter( (array) cet_ece_get( 'qualifications', $id ) );
	// Highest degree first (Ph.D., then master's, then bachelor's), newest first within a level.
	usort( $quals, function ( $a, $b ) {
		$rank = function ( $d ) {
			$d = strtolower( preg_replace( '/[^a-z]/i', '', (string) $d ) );
			if ( preg_match( '/^(phd|doctor|postdoc)/', $d ) ) {
				return 0;
			}
			return preg_match( '/^(m|pg)/', $d ) ? 1 : 2;
		};
		return array( $rank( $a['degree'] ?? '' ), -(int) ( $a['year'] ?? 0 ) ) <=> array( $rank( $b['degree'] ?? '' ), -(int) ( $b['year'] ?? 0 ) );
	} );
	foreach ( $quals as $q ) {
		if ( ! empty( $q['degree'] ) ) {
			$rows[] = array( esc_html( $q['degree'] ), esc_html( $q['specialisation'] ?? '' ), esc_html( $q['institution'] ?? '' ), esc_html( $q['year'] ?? '' ) );
		}
	}
	$main .= cet_ece_section( 'Qualifications', cet_ece_table( array( 'Degree', 'Specialisation', 'Institution', 'Year' ), $rows ) );

	$pubs = cet_ece_ids( cet_ece_get( 'selected_publications', $id ) );
	if ( $pubs ) {
		$list = '<ol class="ece-cites">';
		foreach ( $pubs as $p ) {
			$list .= '<li>' . cet_ece_cite( $p ) . '</li>';
		}
		$list .= '</ol>';
		$all   = get_page_by_path( 'research/publications' );
		if ( $all ) {
			$list .= '<p><a class="ece-more" href="' . esc_url( add_query_arg( 'pub_fac', $id, get_permalink( $all ) ) ) . '">All publications by ' . esc_html( $name ) . '</a></p>';
		}
		$main .= cet_ece_section( 'Selected publications', $list );
	}

	$teach   = '';
	$courses = (array) cet_ece_get( 'courses', $id );
	if ( array_filter( $courses ) ) {
		$teach = '<ul>';
		foreach ( $courses as $c ) {
			if ( ! empty( $c['name'] ) ) {
				$teach .= '<li>' . esc_html( trim( ( $c['code'] ?? '' ) . ' ' . $c['name'] ) ) . '</li>';
			}
		}
		$teach .= '</ul>';
	}
	$labinfo = '';
	$labs    = cet_ece_faculty_labs( $id );
	$guided  = cet_ece_get( 'phd_guided', $id );
	if ( $labs || $guided || cet_ece_get( 'is_guide', $id ) ) {
		$labinfo = '<ul>';
		foreach ( $labs as $l ) {
			$labinfo .= '<li>Lab: <a href="' . esc_url( get_permalink( $l ) ) . '">' . esc_html( get_the_title( $l ) ) . '</a></li>';
		}
		if ( cet_ece_get( 'is_guide', $id ) ) {
			$labinfo .= '<li>Approved Ph.D. guide</li>';
		}
		if ( $guided ) {
			$labinfo .= '<li>Ph.D. scholars guided: ' . esc_html( $guided ) . '</li>';
		}
		$labinfo .= '</ul>';
	}
	if ( $teach || $labinfo ) {
		$main .= '<div class="ece-two">' . cet_ece_section( 'Teaching', $teach ) . cet_ece_section( 'Lab and research supervision', $labinfo ) . '</div>';
	}

	$archive = get_post_type_archive_link( 'faculty' );
	$h       = cet_ece_crumbs( array( array( 'Home', home_url( '/' ) ), array( 'Faculty', $archive ), array( $name, '' ) ) );
	$h      .= '<div class="ece-layout"><aside class="ece-layout-side">' . $aside . '</aside><div class="ece-layout-main">' . $main . '</div></div>';
	return '<div class="ece-profile">' . $h . '</div>';
}

/* ---------- labs ---------- */

function cet_ece_lab_card( $id ) {
	$type  = cet_ece_get( 'lab_type', $id );
	$img   = get_post_thumbnail_id( $id ) ? cet_ece_image( get_post_thumbnail_id( $id ), 'medium_large', get_the_title( $id ), 'ece-lcard-img' ) : '';
	$progs = get_the_terms( $id, 'programme' );
	$tags  = $progs && ! is_wp_error( $progs ) ? implode( ' · ', wp_list_pluck( $progs, 'name' ) ) : '';
	$h     = '<article class="ece-lcard" data-type="' . esc_attr( 'research' === $type ? 'research' : 'teaching' ) . '" data-progs="' . esc_attr( cet_ece_term_slugs( $id, 'programme' ) ) . '">' . $img . '<div class="ece-lcard-body">';
	$h    .= '<span>' . cet_ece_badge( 'research' === $type ? 'Research lab' : 'Teaching lab', 'research' === $type ) . '</span>';
	$h    .= '<h3><a href="' . esc_url( get_permalink( $id ) ) . '">' . esc_html( get_the_title( $id ) ) . '</a></h3>';
	if ( cet_ece_get( 'summary', $id ) ) {
		$h .= '<p>' . esc_html( cet_ece_get( 'summary', $id ) ) . '</p>';
	}
	if ( $tags ) {
		$h .= '<p class="ece-muted ece-small">' . esc_html( $tags ) . '</p>';
	}
	return $h . '</div></article>';
}

function cet_ece_render_lab_list( $attributes ) {
	$type         = $attributes['type'] ?? '';
	$prog         = $attributes['programme'] ?? '';
	$show_filters = ! empty( $attributes['showFilters'] );
	$area         = cet_ece_current_term();
	if ( $show_filters ) {
		$type = cet_ece_get_param( 'l_type' ) ? cet_ece_get_param( 'l_type' ) : $type;
		$prog = cet_ece_get_param( 'l_prog' ) ? cet_ece_get_param( 'l_prog' ) : $prog;
	}
	$args = array( 'post_type' => 'lab', 'posts_per_page' => -1, 'fields' => 'ids', 'orderby' => 'title', 'order' => 'ASC', 'no_found_rows' => true );
	$tax  = array();
	if ( $prog ) {
		$tax[] = array( 'taxonomy' => 'programme', 'field' => 'slug', 'terms' => $prog );
	}
	if ( $area ) {
		$tax[] = array( 'taxonomy' => 'research_area', 'field' => 'slug', 'terms' => $area );
	}
	if ( $tax ) {
		$args['tax_query'] = $tax; // phpcs:ignore WordPress.DB.SlowDBQuery
	}
	$ids = get_posts( $args );

	$h        = '';
	$complete = ! $show_filters || ( ! cet_ece_get_param( 'l_type' ) && ! cet_ece_get_param( 'l_prog' ) );
	if ( $show_filters ) {
		wp_enqueue_script( 'cet-ece-filters' );
		$h .= '<form class="ece-filters" method="get" aria-label="Filter labs"><div class="ece-field"><label for="l_type">Type</label><select id="l_type" name="l_type">';
		foreach ( array( '' => 'All labs', 'teaching' => 'Teaching labs', 'research' => 'Research labs' ) as $k => $v ) {
			$h .= '<option value="' . esc_attr( $k ) . '"' . selected( $type, $k, false ) . '>' . esc_html( $v ) . '</option>';
		}
		$h    .= '</select></div><div class="ece-field"><label for="l_prog">Programme</label><select id="l_prog" name="l_prog"><option value="">All programmes</option>';
		$terms = get_terms( array( 'taxonomy' => 'programme', 'hide_empty' => false ) );
		if ( ! is_wp_error( $terms ) ) {
			foreach ( $terms as $t ) {
				$h .= '<option value="' . esc_attr( $t->slug ) . '"' . selected( $prog, $t->slug, false ) . '>' . esc_html( $t->name ) . '</option>';
			}
		}
		$h .= '</select></div><div class="ece-field ece-field-btn"><button type="submit" class="wp-element-button">Show</button></div></form>';
	}

	$sets = array(
		'teaching' => array( 'Teaching labs', 'Each page lists the courses, experiments, equipment and lab manual.' ),
		'research' => array( 'Research labs', 'Each page lists the research focus, people, projects and facilities.' ),
	);
	$any  = false;
	foreach ( $sets as $k => $label ) {
		if ( $type && $type !== $k ) {
			continue;
		}
		$list = array_filter( $ids, function ( $id ) use ( $k ) {
			$t = cet_ece_get( 'lab_type', $id );
			return ( $t ? $t : 'teaching' ) === $k;
		} );
		if ( ! $list ) {
			continue;
		}
		$any = true;
		// Labs with a photo first (the complete entries), then the rest; each group by name.
		usort( $list, function ( $a, $b ) {
			return array( get_post_thumbnail_id( $a ) ? 0 : 1, strtolower( get_the_title( $a ) ) ) <=> array( get_post_thumbnail_id( $b ) ? 0 : 1, strtolower( get_the_title( $b ) ) );
		} );
		$h  .= '<section class="ece-sec">' . ( $type ? '' : '<h2>' . esc_html( $label[0] ) . ' <span class="ece-count">' . count( $list ) . '</span></h2><p class="ece-muted">' . esc_html( $label[1] ) . '</p>' ) . '<div class="ece-grid ece-grid-cards">';
		foreach ( $list as $id ) {
			$h .= cet_ece_lab_card( $id );
		}
		$h .= '</div></section>';
	}
	if ( ! $any ) {
		$h .= '<p class="ece-empty">' . ( $area ? 'No labs in this research area yet.' : 'No labs to show.' ) . '</p>';
	}
	return '<div class="ece-lab-list" data-complete="' . ( $complete ? '1' : '0' ) . '">' . $h . '</div>';
}

function cet_ece_render_lab_details( $attributes, $content, $block ) {
	$id = $block->context['postId'] ?? get_the_ID();
	if ( ! $id || 'lab' !== get_post_type( $id ) ) {
		return '';
	}
	$name     = get_the_title( $id );
	$research = 'research' === cet_ece_get( 'lab_type', $id );
	$lead     = (int) cet_ece_get( 'lead_faculty', $id );
	$staff    = cet_ece_ids( cet_ece_get( 'tech_staff', $id ) );
	$progs    = get_the_terms( $id, 'programme' );

	$badges = cet_ece_badge( $research ? 'Research lab' : 'Teaching lab', $research );
	if ( $progs && ! is_wp_error( $progs ) ) {
		foreach ( $progs as $p ) {
			$badges .= ' ' . cet_ece_badge( $p->name );
		}
	}
	$staff_names = implode( ', ', array_map( 'get_the_title', $staff ) );
	$scholars    = array_filter( (array) cet_ece_get( 'scholars', $id ) );
	$projects    = array_filter( (array) cet_ece_get( 'projects', $id ) );
	$facts       = $research
		? array( 'Location' => esc_html( cet_ece_get( 'location', $id ) ), 'Lead faculty' => cet_ece_faculty_link( $lead ), 'Research scholars' => $scholars ? (string) count( $scholars ) : '', 'Funded projects' => $projects ? (string) count( $projects ) : '' )
		: array( 'Location' => esc_html( cet_ece_get( 'location', $id ) ), 'Lab in charge' => cet_ece_faculty_link( $lead ), 'Technical staff' => esc_html( $staff_names ), 'Workstations' => esc_html( cet_ece_get( 'workstations', $id ) ) );

	$band  = '<div class="ece-band-inner">' . cet_ece_crumbs( array( array( 'Home', home_url( '/' ) ), array( 'Laboratories', get_post_type_archive_link( 'lab' ) ), array( $name, '' ) ) );
	$band .= '<div class="ece-badges">' . $badges . '</div><h1>' . esc_html( $name ) . '</h1>';
	if ( cet_ece_get( 'summary', $id ) ) {
		$band .= '<p class="ece-lead">' . esc_html( cet_ece_get( 'summary', $id ) ) . '</p>';
	}
	$band .= cet_ece_facts( $facts ) . '</div>';

	$main = '';
	if ( get_post_thumbnail_id( $id ) ) {
		$main .= '<figure class="ece-lab-photo">' . cet_ece_image( get_post_thumbnail_id( $id ), 'large', 'Photo of the ' . $name ) . '</figure>';
	}
	$body = trim( get_post_field( 'post_content', $id ) );
	if ( $body ) {
		$main .= '<div class="ece-prose">' . apply_filters( 'the_content', $body ) . '</div>'; // phpcs:ignore WordPress.NamingConventions.PrefixAllGlobals
	}
	if ( $research ) {
		$main .= cet_ece_section( 'Research areas', cet_ece_term_chips( $id ) );
		$people = array_unique( array_merge( $lead ? array( $lead ) : array(), cet_ece_ids( cet_ece_get( 'members', $id ) ) ) );
		if ( $people ) {
			$cards = '<div class="ece-grid">';
			foreach ( $people as $p ) {
				$cards .= cet_ece_faculty_card( $p );
			}
			$main .= cet_ece_section( 'Faculty', $cards . '</div>' );
		}
		$rows = array();
		foreach ( $scholars as $s ) {
			if ( ! empty( $s['name'] ) ) {
				$rows[] = array( esc_html( $s['name'] ), 'mtech' === ( $s['level'] ?? '' ) ? 'M.Tech' : 'Ph.D.', cet_ece_faculty_link( (int) ( $s['guide'] ?? 0 ) ), esc_html( $s['topic'] ?? '' ), 'completed' === ( $s['status'] ?? '' ) ? 'Completed' : 'Ongoing' );
			}
		}
		$main .= cet_ece_section( 'Research scholars', cet_ece_table( array( 'Name', 'Programme', 'Guide', 'Topic', 'Status' ), $rows ) );
		$main .= cet_ece_section( 'Funded projects', cet_ece_projects_table( array( $id ) ) );
	} else {
		$rows = array();
		foreach ( (array) cet_ece_get( 'courses', $id ) as $c ) {
			if ( ! empty( $c['name'] ) ) {
				$rows[] = array( esc_html( $c['code'] ?? '' ), esc_html( $c['name'] ), esc_html( $c['programme'] ?? '' ), esc_html( $c['semester'] ?? '' ) );
			}
		}
		$main .= cet_ece_section( 'Courses served', cet_ece_table( array( 'Course code', 'Course', 'Programme', 'Semester' ), $rows ) );
		$exp   = array_filter( array_map( 'trim', explode( "\n", (string) cet_ece_get( 'experiments', $id ) ) ) );
		if ( $exp ) {
			$list = '<ol>';
			foreach ( $exp as $e ) {
				$list .= '<li>' . esc_html( $e ) . '</li>';
			}
			$main .= cet_ece_section( 'Experiments', $list . '</ol>' );
		}
	}
	$rows = array();
	foreach ( (array) cet_ece_get( 'equipment', $id ) as $e ) {
		if ( ! empty( $e['name'] ) ) {
			$rows[] = array( esc_html( $e['name'] ), esc_html( $e['make_model'] ?? '' ), esc_html( $e['quantity'] ?? '' ) );
		}
	}
	$main .= cet_ece_section( $research ? 'Facilities' : 'Major equipment', cet_ece_table( array( 'Item', 'Make and model or details', 'Quantity' ), $rows ) );

	if ( ! $body && ! cet_ece_get( 'courses', $id ) && ! cet_ece_get( 'equipment', $id ) && ! $scholars && ! $projects ) {
		$main .= '<p class="ece-muted">Details of this lab (courses, equipment and people) are being added.</p>';
	}
	$aside     = '';
	$downloads = cet_ece_file_link( cet_ece_get( 'manual', $id ), 'Lab manual (PDF)' ) . cet_ece_file_link( cet_ece_get( 'timetable', $id ), 'Lab timetable (PDF)' ) . cet_ece_file_link( cet_ece_get( 'safety_file', $id ), 'Safety rules (PDF)' );
	$aside    .= cet_ece_side_card( 'Downloads', $downloads );
	if ( $lead ) {
		$email  = cet_ece_get( 'email', $lead );
		$aside .= cet_ece_side_card( $research ? 'Contact' : 'Lab in charge', cet_ece_faculty_link( $lead ) . ( $email ? '<a href="mailto:' . esc_attr( antispambot( $email ) ) . '">' . esc_html( antispambot( $email ) ) . '</a>' : '' ) );
	}
	if ( $research && cet_ece_get( 'join_text', $id ) ) {
		$aside .= cet_ece_side_card( 'Join the lab', '<p>' . esc_html( cet_ece_get( 'join_text', $id ) ) . '</p>' );
	}
	if ( $research && cet_ece_get( 'collaborations', $id ) ) {
		$aside .= cet_ece_side_card( 'Collaborations', '<p>' . esc_html( cet_ece_get( 'collaborations', $id ) ) . '</p>' );
	}
	if ( cet_ece_get( 'safety_text', $id ) ) {
		$aside .= cet_ece_side_card( 'Safety', '<p>' . nl2br( esc_html( cet_ece_get( 'safety_text', $id ) ) ) . '</p>' );
	}

	return '<div class="ece-lab"><div class="ece-band">' . $band . '</div><div class="ece-wrap"><div class="ece-layout ece-layout-rev"><div class="ece-layout-main">' . $main . '</div><aside class="ece-layout-side">' . $aside . '</aside></div></div></div>';
}

/* ---------- projects ---------- */

function cet_ece_projects_table( $lab_ids = null ) {
	if ( null === $lab_ids ) {
		$lab_ids = get_posts( array( 'post_type' => 'lab', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true ) );
	}
	$rows = array();
	foreach ( $lab_ids as $lab ) {
		foreach ( array_filter( (array) cet_ece_get( 'projects', $lab ) ) as $p ) {
			if ( empty( $p['title'] ) ) {
				continue;
			}
			$period = trim( ( $p['start_year'] ?? '' ) . ( ! empty( $p['end_year'] ) ? '–' . $p['end_year'] : '' ) );
			$rows[] = array(
				'sort' => array( 'completed' === ( $p['status'] ?? '' ) ? 1 : 0, -1 * (int) ( $p['start_year'] ?? 0 ) ),
				'row'  => array( esc_html( $p['title'] ), cet_ece_faculty_link( (int) ( $p['investigator'] ?? 0 ) ), esc_html( $p['agency'] ?? '' ), esc_html( $period ), 'completed' === ( $p['status'] ?? '' ) ? cet_ece_badge( 'Completed' ) : cet_ece_badge( 'Ongoing', true ) ),
			);
		}
	}
	usort( $rows, function ( $a, $b ) {
		return $a['sort'] <=> $b['sort'];
	} );
	return cet_ece_table( array( 'Project', 'Investigator', 'Funding agency', 'Period', 'Status' ), wp_list_pluck( $rows, 'row' ) );
}

function cet_ece_render_projects() {
	$t = cet_ece_projects_table();
	if ( $t ) {
		return '<div class="ece-projects">' . $t . '</div>';
	}
	return current_user_can( 'edit_posts' )
		? '<p class="ece-empty">Funded projects appear here once they are added to a research lab (Labs › edit a research lab › Funded projects).</p>'
		: '<p class="ece-empty">No funded projects are listed yet.</p>';
}

/**
 * Research figures, counted from the site's own records so they never go stale:
 * approved guides (faculty marked as guides), Ph.D. scholars (ongoing, in research
 * labs), ongoing funded projects, and last year's publications. A figure that is
 * zero is left out rather than shown as 0.
 */
function cet_ece_render_research_figures() {
	$faculty  = get_posts( array( 'post_type' => 'faculty', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true ) );
	$guides   = count( array_filter( $faculty, function ( $id ) {
		return (bool) cet_ece_get( 'is_guide', $id );
	} ) );
	$scholars = 0;
	$projects = 0;
	foreach ( get_posts( array( 'post_type' => 'lab', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true ) ) as $lab ) {
		foreach ( array_filter( (array) cet_ece_get( 'scholars', $lab ) ) as $s ) {
			$scholars += ( 'phd' === ( $s['level'] ?? 'phd' ) && 'completed' !== ( $s['status'] ?? '' ) ) ? 1 : 0;
		}
		foreach ( array_filter( (array) cet_ece_get( 'projects', $lab ) ) as $p ) {
			$projects += ( ! empty( $p['title'] ) && 'completed' !== ( $p['status'] ?? '' ) ) ? 1 : 0;
		}
	}
	$last = (int) wp_date( 'Y' ) - 1;
	$pubs = count( get_posts( array( 'post_type' => 'publication', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true, 'meta_key' => 'year', 'meta_value' => $last ) ) ); // phpcs:ignore WordPress.DB.SlowDBQuery
	$items = array(
		array( $guides, 'Approved research guides' ),
		array( $scholars, 'Ph.D. scholars' ),
		array( $projects, 'Funded projects, ongoing' ),
		array( $pubs, 'Publications in ' . $last ),
	);
	$h = '';
	foreach ( $items as $it ) {
		if ( $it[0] > 0 ) {
			$h .= '<div class="ece-figure"><p class="ece-stat-number">' . (int) $it[0] . '</p><p class="ece-stat-label">' . esc_html( $it[1] ) . '</p></div>';
		}
	}
	return $h ? '<div class="ece-figures">' . $h . '</div>' : '';
}

/* ---------- staff advisors ---------- */

function cet_ece_render_staff_advisors( $attributes ) {
	$show_past = ! empty( $attributes['type'] ) && 'past' === $attributes['type'];
	$ids       = get_posts( array( 'post_type' => 'batch', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true ) );
	$by_prog   = array();
	foreach ( $ids as $id ) {
		$prog = cet_ece_get( 'programme', $id );
		$year = (int) cet_ece_get( 'admission_year', $id );
		if ( cet_ece_batch_is_current( $prog, $year ) === $show_past ) {
			continue;
		}
		$by_prog[ $prog ][] = $id;
	}
	$progs = cet_ece_programmes();
	$h     = '';
	foreach ( $progs as $key => $p ) {
		if ( empty( $by_prog[ $key ] ) ) {
			continue;
		}
		$list = $by_prog[ $key ];
		usort( $list, function ( $a, $b ) {
			$y = (int) cet_ece_get( 'admission_year', $b ) <=> (int) cet_ece_get( 'admission_year', $a );
			return $y ? $y : strcmp( (string) cet_ece_get( 'batch_label', $a ), (string) cet_ece_get( 'batch_label', $b ) );
		} );
		$rows = array();
		foreach ( $list as $id ) {
			$year     = (int) cet_ece_get( 'admission_year', $id );
			$advisors = cet_ece_ids( cet_ece_get( 'advisors', $id ) );
			$names    = implode( '<br>', array_map( 'cet_ece_faculty_link', $advisors ) );
			$emails   = implode( '<br>', array_map( function ( $a ) {
				$e = cet_ece_get( 'email', $a );
				return $e ? '<a href="mailto:' . esc_attr( antispambot( $e ) ) . '">' . esc_html( antispambot( $e ) ) . '</a>' : '';
			}, $advisors ) );
			$when   = 2 === $p[2] ? $year . '–' . substr( (string) ( $year + 2 ), -2 ) : (string) $year;
			$label  = cet_ece_get( 'batch_label', $id );
			$rows[] = array( esc_html( $when ), esc_html( $label ? $label : '–' ), $names, $emails );
		}
		$table = cet_ece_table( array( 2 === $p[2] ? 'Session' : 'Admitted', 'Batch', 'Staff advisor', 'Email' ), $rows );
		$h    .= $show_past
			? '<details class="ece-details"><summary>' . esc_html( $p[0] ) . ' <span class="ece-count">' . count( $rows ) . '</span></summary>' . $table . '</details>'
			: cet_ece_section( $p[0], $table );
	}
	if ( ! $h ) {
		return '<p class="ece-empty">' . ( $show_past ? 'No past batches recorded yet.' : 'No current batches recorded yet.' ) . '</p>';
	}
	return '<div class="ece-advisors">' . $h . '</div>';
}

/* ---------- publications ---------- */

function cet_ece_publication_query( $attributes ) {
	$show_filters = ! isset( $attributes['showFilters'] ) || $attributes['showFilters'];
	$f            = array(
		'q'    => $show_filters ? cet_ece_get_param( 'pub_q' ) : '',
		'year' => $show_filters ? cet_ece_get_param( 'pub_year' ) : '',
		'type' => $show_filters ? cet_ece_get_param( 'pub_type' ) : '',
		'fac'  => $show_filters ? absint( cet_ece_get_param( 'pub_fac' ) ) : 0,
		'area' => cet_ece_current_term(),
	);
	$args = array(
		'post_type'      => 'publication',
		'posts_per_page' => ! empty( $attributes['limit'] ) ? (int) $attributes['limit'] : -1,
		'fields'         => 'ids',
		'no_found_rows'  => true,
		'meta_key'       => 'year', // phpcs:ignore WordPress.DB.SlowDBQuery
		'orderby'        => array( 'meta_value_num' => 'DESC', 'title' => 'ASC' ),
	);
	$meta = array();
	if ( $f['q'] ) {
		$args['s'] = $f['q'];
	}
	if ( $f['year'] ) {
		$meta[] = 'earlier' === $f['year'] ? array( 'key' => 'year', 'value' => (int) wp_date( 'Y' ) - 2, 'compare' => '<', 'type' => 'NUMERIC' ) : array( 'key' => 'year', 'value' => (int) $f['year'], 'type' => 'NUMERIC' );
	}
	if ( $f['type'] ) {
		$meta[] = array( 'key' => 'pub_type', 'value' => $f['type'] );
	}
	if ( $f['fac'] ) {
		$meta[] = array( 'key' => 'faculty', 'value' => '"' . $f['fac'] . '"', 'compare' => 'LIKE' );
	}
	if ( $meta ) {
		$args['meta_query'] = $meta; // phpcs:ignore WordPress.DB.SlowDBQuery
	}
	if ( $f['area'] ) {
		$args['tax_query'] = array( array( 'taxonomy' => 'research_area', 'field' => 'slug', 'terms' => $f['area'] ) ); // phpcs:ignore WordPress.DB.SlowDBQuery
	}
	return array( get_posts( $args ), $f, $show_filters );
}

function cet_ece_render_publications( $attributes ) {
	list( $ids, $f, $show_filters ) = cet_ece_publication_query( $attributes );
	$h = '';
	if ( $show_filters && ! is_tax() ) {
		$this_year = (int) wp_date( 'Y' );
		wp_enqueue_script( 'cet-ece-filters' );
		$h        .= '<form class="ece-filters" method="get" role="search" aria-label="Filter publications" data-earlier="' . ( $this_year - 2 ) . '">';
		$h        .= '<div class="ece-field ece-field-wide"><label for="pub_q">Search title</label><input id="pub_q" name="pub_q" type="search" value="' . esc_attr( $f['q'] ) . '"></div>';
		$h        .= '<div class="ece-field"><label for="pub_year">Year</label><select id="pub_year" name="pub_year"><option value="">All years</option>';
		for ( $y = $this_year; $y > $this_year - 3; $y-- ) {
			$h .= '<option value="' . $y . '"' . selected( $f['year'], (string) $y, false ) . '>' . $y . '</option>';
		}
		$h .= '<option value="earlier"' . selected( $f['year'], 'earlier', false ) . '>Earlier</option></select></div>';
		$h .= '<div class="ece-field"><label for="pub_type">Type</label><select id="pub_type" name="pub_type"><option value="">All types</option>';
		foreach ( cet_ece_pub_types() as $k => $v ) {
			$h .= '<option value="' . esc_attr( $k ) . '"' . selected( $f['type'], $k, false ) . '>' . esc_html( $v ) . '</option>';
		}
		$h      .= '</select></div><div class="ece-field"><label for="pub_fac">Faculty</label><select id="pub_fac" name="pub_fac"><option value="">All faculty</option>';
		$faculty = get_posts( array( 'post_type' => 'faculty', 'posts_per_page' => -1, 'fields' => 'ids', 'orderby' => 'title', 'order' => 'ASC', 'no_found_rows' => true ) );
		foreach ( $faculty as $fid ) {
			$h .= '<option value="' . (int) $fid . '"' . selected( $f['fac'], $fid, false ) . '>' . esc_html( get_the_title( $fid ) ) . '</option>';
		}
		$h .= '</select></div><div class="ece-field ece-field-btn"><button type="submit" class="wp-element-button">Show</button></div></form>';
		if ( $ids ) {
			$h .= '<p class="ece-toolbar"><span class="ece-muted">' . count( $ids ) . ' ' . _n( 'publication', 'publications', count( $ids ), 'cet-ece-core' ) . ', newest first</span> <a class="ece-btn-outline" href="' . esc_url( add_query_arg( 'ece_bibtex', '1' ) ) . '">Download BibTeX</a></p>';
		}
	}
	if ( ! $ids ) {
		$msg = is_tax() ? 'No publications in this research area yet.' : ( array_filter( array( $f['q'], $f['year'], $f['type'], $f['fac'] ) ) ? 'No publications match these filters.' : 'No publications listed yet.' );
		return '<div class="ece-pubs">' . $h . '<p class="ece-empty">' . esc_html( $msg ) . '</p></div>';
	}
	$by_year = array();
	foreach ( $ids as $id ) {
		$by_year[ (int) cet_ece_get( 'year', $id ) ][] = $id;
	}
	krsort( $by_year );
	$types = cet_ece_pub_types();
	foreach ( $by_year as $year => $list ) {
		$h .= '<section class="ece-sec"><h2>' . esc_html( $year ? $year : 'Undated' ) . ' <span class="ece-count">' . count( $list ) . '</span></h2><ol class="ece-cites">';
		foreach ( $list as $id ) {
			$t  = cet_ece_get( 'pub_type', $id );
			$h .= '<li data-year="' . (int) $year . '" data-type="' . esc_attr( $t ) . '" data-fac="' . esc_attr( implode( ' ', cet_ece_ids( cet_ece_get( 'faculty', $id ) ) ) ) . '">' . cet_ece_cite( $id ) . ( isset( $types[ $t ] ) ? ' ' . cet_ece_badge( $types[ $t ] ) : '' ) . '</li>';
		}
		$h .= '</ol></section>';
	}
	$complete = ! array_filter( array( $f['q'], $f['year'], $f['type'], $f['fac'] ) );
	return '<div class="ece-pubs" data-complete="' . ( $complete ? '1' : '0' ) . '">' . $h . '</div>';
}

/* ---------- research areas ---------- */

function cet_ece_render_research_areas() {
	$terms = get_terms( array( 'taxonomy' => 'research_area', 'hide_empty' => false ) );
	if ( is_wp_error( $terms ) || ! $terms ) {
		return '';
	}
	$h = '<div class="ece-chips ece-chips-lg">';
	foreach ( $terms as $t ) {
		$h .= '<a class="ece-chip" href="' . esc_url( get_term_link( $t ) ) . '">' . esc_html( $t->name ) . '</a>';
	}
	return $h . '</div>';
}

/* ---------- technical staff ---------- */

function cet_ece_render_tech_staff() {
	$ids = get_posts( array( 'post_type' => 'staff', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true ) );
	if ( ! $ids ) {
		return '<p class="ece-empty">No technical staff added yet.</p>';
	}
	$labs_for = array();
	$labs     = get_posts( array( 'post_type' => 'lab', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true ) );
	foreach ( $labs as $lab ) {
		foreach ( cet_ece_ids( cet_ece_get( 'tech_staff', $lab ) ) as $s ) {
			$labs_for[ $s ][] = '<a href="' . esc_url( get_permalink( $lab ) ) . '">' . esc_html( get_the_title( $lab ) ) . '</a>';
		}
	}
	$h = '';
	foreach ( cet_ece_staff_categories() as $key => $names ) {
		$list = array_filter( $ids, function ( $id ) use ( $key ) {
			return cet_ece_get( 'staff_category', $id ) === $key;
		} );
		if ( ! $list ) {
			continue;
		}
		$rows = array();
		foreach ( cet_ece_sort_people( array_values( $list ) ) as $id ) {
			$rows[] = array( esc_html( get_the_title( $id ) ), esc_html( $names[0] ), implode( ', ', $labs_for[ $id ] ?? array() ) );
		}
		$h .= '<section class="ece-sec"><h2>' . esc_html( $names[1] ) . ' <span class="ece-count">' . count( $rows ) . '</span></h2>' . cet_ece_table( array( 'Name', 'Designation', 'Assigned lab' ), $rows ) . '</section>';
	}
	return '<div class="ece-staff">' . $h . '</div>';
}
