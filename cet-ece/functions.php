<?php
/**
 * CET ECE theme functions.
 *
 * Keep this file small. Content types, fields and dynamic blocks live in the
 * CET ECE Core plugin so they survive a future theme change.
 *
 * @package cet-ece
 */

defined( 'ABSPATH' ) || exit;

define( 'CET_ECE_THEME_VERSION', '1.0.0' );

/**
 * Theme supports and editor styles.
 */
add_action( 'after_setup_theme', function () {
	add_theme_support( 'wp-block-styles' );
	add_theme_support( 'editor-styles' );
	add_editor_style( 'assets/css/theme.css' );
	remove_theme_support( 'core-block-patterns' );
	add_post_type_support( 'page', 'excerpt' );
} );

/**
 * Colour tokens and small layout rules, on the site and in the admin
 * (the admin needs the tokens so colour swatches show correctly).
 */
function cet_ece_enqueue_tokens() {
	wp_enqueue_style( 'cet-ece', get_theme_file_uri( 'assets/css/theme.css' ), array(), CET_ECE_THEME_VERSION );
}
add_action( 'wp_enqueue_scripts', 'cet_ece_enqueue_tokens' );
add_action( 'admin_enqueue_scripts', 'cet_ece_enqueue_tokens' );

/**
 * Pattern categories.
 */
add_action( 'init', function () {
	register_block_pattern_category( 'cet-ece-pages', array( 'label' => __( 'ECE: full pages', 'cet-ece' ) ) );
	register_block_pattern_category( 'cet-ece-sections', array( 'label' => __( 'ECE: sections', 'cet-ece' ) ) );
} );

/**
 * Starter pages.
 *
 * On first activation, create the site's pages from the theme's page patterns,
 * set the homepage and the news page, and add the news categories. Pages that
 * already exist (matched by slug) are left alone, so this is safe to rerun.
 */
function cet_ece_starter_pages() {
	return array(
		// slug, title, pattern, parent slug.
		array( 'home', 'Home', 'cet-ece/page-home', '' ),
		array( 'about', 'About', 'cet-ece/page-about', '' ),
		array( 'academics', 'Academics', 'cet-ece/page-academics', '' ),
		array( 'btech-ece', 'B.Tech in Electronics and Communication Engineering', 'cet-ece/page-programme', 'academics' ),
		array( 'btech-aei', 'B.Tech in Applied Electronics and Instrumentation', 'cet-ece/page-programme', 'academics' ),
		array( 'mtech-applied-electronics', 'M.Tech in Applied Electronics and Instrumentation', 'cet-ece/page-programme', 'academics' ),
		array( 'mtech-communication-systems', 'M.Tech in Communication Systems', 'cet-ece/page-programme', 'academics' ),
		array( 'mtech-signal-processing', 'M.Tech in Signal Processing', 'cet-ece/page-programme', 'academics' ),
		array( 'mtech-micro-nano-electronics', 'M.Tech in Micro and Nano Electronics', 'cet-ece/page-programme', 'academics' ),
		array( 'mtech-robotics-automation', 'M.Tech in Robotics and Automation', 'cet-ece/page-programme', 'academics' ),
		array( 'phd', 'Ph.D. in Electronics and Communication Engineering', 'cet-ece/page-phd', 'academics' ),
		array( 'obe', 'Outcome-based education', 'cet-ece/page-obe', 'academics' ),
		array( 'staff-advisors', 'Staff advisors', 'cet-ece/page-staff-advisors', '' ),
		array( 'technical-staff', 'Technical staff', 'cet-ece/page-technical-staff', '' ),
		array( 'research', 'Research', 'cet-ece/page-research', '' ),
		array( 'publications', 'Publications', 'cet-ece/page-publications', 'research' ),
		array( 'library', 'Library', 'cet-ece/page-library', '' ),
		array( 'placements', 'Placements', 'cet-ece/page-placements', '' ),
		array( 'students', 'Students', 'cet-ece/page-students', '' ),
		array( 'contact', 'Contact', 'cet-ece/page-contact', '' ),
		array( 'news', 'News and Events', '', '' ),
	);
}

/**
 * Lead sentences shown under page titles (stored as the page excerpt) and
 * programme facts filled into the programme pattern.
 */
function cet_ece_starter_leads() {
	return array(
		'about'                        => 'Established at the Sreekariyam campus in 1964–65 with an intake of 33 students. Today the department offers two B.Tech programmes, five M.Tech specialisations and a doctoral programme.',
		'academics'                    => 'Two B.Tech programmes, five M.Tech specialisations and a doctoral programme, all affiliated to APJ Abdul Kalam Technological University.',
		'btech-ece'                    => 'A four-year programme in electronics, communication, signal processing and embedded systems.',
		'btech-aei'                    => 'A four-year programme in electronics, instrumentation and control.',
		'mtech-applied-electronics'    => 'A two-year postgraduate programme in applied electronics and instrumentation.',
		'mtech-communication-systems'  => 'A two-year postgraduate programme, formerly Microwave and Television Engineering.',
		'mtech-signal-processing'      => 'A two-year postgraduate programme in signal processing.',
		'mtech-micro-nano-electronics' => 'A two-year postgraduate programme in micro and nano electronics.',
		'mtech-robotics-automation'    => 'A two-year interdisciplinary postgraduate programme in robotics and automation.',
		'phd'                          => 'Full-time and part-time doctoral research under APJ Abdul Kalam Technological University.',
		'obe'                          => 'Vision, mission and outcomes for each programme, with the committees that review them and the yearly attainment reports.',
		'staff-advisors'               => 'Current batches and their faculty advisors.',
		'technical-staff'              => 'The staff who run the department’s laboratories.',
		'research'                     => 'Research in signal processing, communication, optics, biomedical engineering, power electronics, machine learning and VLSI.',
		'publications'                 => 'Journal and conference papers by faculty and research scholars, in IEEE style with DOI links.',
		'library'                      => 'Books, journals and e-resources for the department’s programmes.',
		'placements'                   => 'Placement results for B.Tech ECE and AEI, year by year, with the companies that recruit from the department.',
		'students'                     => 'Notices, calendars, syllabus and contacts for current students.',
		'contact'                      => 'Department of Electronics and Communication Engineering, College of Engineering Trivandrum.',
	);
}

function cet_ece_programme_facts() {
	// slug => intake, duration, programme taxonomy slug for the labs list.
	return array(
		'btech-ece'                    => array( '120 + 12 lateral entry [confirm]', '4 years, 8 semesters', 'btech-ece' ),
		'btech-aei'                    => array( '60 + 6 lateral entry [confirm]', '4 years, 8 semesters', 'btech-aei' ),
		'mtech-applied-electronics'    => array( '18', '2 years, 4 semesters', 'mtech' ),
		'mtech-communication-systems'  => array( '18', '2 years, 4 semesters', 'mtech' ),
		'mtech-signal-processing'      => array( '18', '2 years, 4 semesters', 'mtech' ),
		'mtech-micro-nano-electronics' => array( '18', '2 years, 4 semesters', 'mtech' ),
		'mtech-robotics-automation'    => array( '18', '2 years, 4 semesters', 'mtech' ),
	);
}

function cet_ece_create_starter_content() {
	if ( get_option( 'cet_ece_starter_done' ) ) {
		return;
	}
	$registry = WP_Block_Patterns_Registry::get_instance();
	$ids      = array();

	foreach ( cet_ece_starter_pages() as $row ) {
		list( $slug, $title, $pattern, $parent ) = $row;
		$path     = $parent ? $parent . '/' . $slug : $slug;
		$existing = get_page_by_path( $path );
		if ( $existing ) {
			$ids[ $slug ] = $existing->ID;
			continue;
		}
		$content = '';
		if ( $pattern && $registry->is_registered( $pattern ) ) {
			$p       = $registry->get_registered( $pattern );
			$content = $p['content'];
		}
		$facts = cet_ece_programme_facts();
		if ( isset( $facts[ $slug ] ) ) {
			$content = str_replace(
				array( '[Intake]', '[Duration]', '"programme":""' ),
				array( $facts[ $slug ][0], $facts[ $slug ][1], '"programme":"' . $facts[ $slug ][2] . '"' ),
				$content
			);
		}
		$leads = cet_ece_starter_leads();
		$ids[ $slug ] = wp_insert_post(
			array(
				'post_type'    => 'page',
				'post_status'  => 'publish',
				'post_title'   => $title,
				'post_name'    => $slug,
				'post_content' => $content,
				'post_excerpt' => $leads[ $slug ] ?? '',
				'post_parent'  => $parent && isset( $ids[ $parent ] ) ? $ids[ $parent ] : 0,
				'page_template' => 'home' === $slug ? 'page-no-title' : '',
			)
		);
	}

	if ( ! empty( $ids['home'] ) && ! empty( $ids['news'] ) ) {
		update_option( 'show_on_front', 'page' );
		update_option( 'page_on_front', $ids['home'] );
		update_option( 'page_for_posts', $ids['news'] );
	}

	foreach ( array( 'Announcements', 'Department news', 'Workshops and FDPs', 'Talks', 'Outreach' ) as $cat ) {
		if ( ! term_exists( $cat, 'category' ) ) {
			wp_insert_term( $cat, 'category' );
		}
	}

	if ( in_array( get_option( 'blogname' ), array( '', 'My WordPress Site', 'WordPress' ), true ) ) {
		update_option( 'blogname', 'Department of Electronics and Communication Engineering' );
	}
	if ( in_array( get_option( 'blogdescription' ), array( '', 'Just another WordPress site' ), true ) ) {
		update_option( 'blogdescription', 'College of Engineering Trivandrum' );
	}
	update_option( 'permalink_structure', '/%postname%/' );
	flush_rewrite_rules();
	update_option( 'cet_ece_starter_done', 1 );
}
add_action( 'after_switch_theme', 'cet_ece_create_starter_content' );
