<?php
/**
 * Sample content for the WordPress Playground demo.
 * Run after the plugin and theme are active. Names and figures are invented;
 * news items are taken from the department's current website.
 */

if ( ! function_exists( 'update_field' ) ) {
	echo 'Secure Custom Fields is not active.';
	return;
}

// Pages, homepage, categories.
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

function demo_post( $type, $title, $fields = array(), $content = '', $extra = array() ) {
	$id = wp_insert_post( array_merge( array(
		'post_type'    => $type,
		'post_status'  => 'publish',
		'post_title'   => $title,
		'post_content' => $content,
	), $extra ) );
	foreach ( $fields as $k => $v ) {
		update_field( $k, $v, $id );
	}
	return $id;
}

function demo_terms( $names, $tax = 'research_area' ) {
	$ids = array();
	foreach ( (array) $names as $n ) {
		$t = get_term_by( 'name', $n, $tax );
		if ( $t ) {
			$ids[] = (int) $t->term_id;
		}
	}
	return $ids;
}

function demo_para( $text ) {
	return '<!-- wp:paragraph --><p>' . esc_html( $text ) . '</p><!-- /wp:paragraph -->';
}

// ---------- Faculty (invented names) ----------
$faculty = array(
	array( 'Dr. Anjali Varma', 'professor', 'Head of Department', 1998, array( 'Signal and image processing', 'Machine learning' ), array( array( 'Ph.D.', 'Signal Processing', 'IIT Madras', 2007 ), array( 'M.Tech', 'Communication Systems', 'College of Engineering Trivandrum', 1997 ) ), array( array( 'ECT401', 'Digital Image Processing' ) ), 1, 8, 'Works on image and video processing, with recent work on learning-based restoration.' ),
	array( 'Dr. Thomas Mathew', 'professor', 'Dean (Research)', 2000, array( 'Communication systems' ), array( array( 'Ph.D.', 'Wireless Communication', 'IISc Bangalore', 2009 ) ), array( array( 'ECT302', 'Electromagnetics' ) ), 1, 6, 'Research in wireless communication and antenna design.' ),
	array( 'Dr. Lakshmi Pillai', 'professor', '', 2003, array( 'VLSI and micro-nano electronics' ), array( array( 'Ph.D.', 'VLSI Design', 'NIT Calicut', 2011 ) ), array( array( 'ECT304', 'VLSI Circuit Design' ) ), 1, 5, 'Works on low-power VLSI circuits and hardware for signal processing.' ),
	array( 'Dr. Suresh Nair', 'associate_professor', '', 2008, array( 'Control and power electronics' ), array( array( 'Ph.D.', 'Power Electronics', 'University of Kerala', 2016 ) ), array( array( 'ECT206', 'Analog Circuits' ) ), 1, 2, 'Research in power converters and motor drives.' ),
	array( 'Dr. Reshmi Krishnan', 'associate_professor', '', 2010, array( 'Optics and photonics' ), array( array( 'Ph.D.', 'Photonics', 'CUSAT', 2017 ) ), array( array( 'ECT401', 'Optical Communication' ) ), 1, 1, 'Works on fibre-optic sensors and optical communication.' ),
	array( 'Dr. Arun George', 'assistant_professor', '', 2015, array( 'Machine learning', 'Signal and image processing' ), array( array( 'Ph.D.', 'Machine Learning', 'IIT Bombay', 2014 ) ), array( array( 'ECT463', 'Machine Learning' ) ), 0, 0, 'Research in audio signal processing and deep learning.' ),
	array( 'Prof. Divya S', 'assistant_professor', '', 2016, array( 'Biomedical engineering' ), array( array( 'M.Tech', 'Applied Electronics', 'College of Engineering Trivandrum', 2012 ) ), array( array( 'ECT203', 'Logic Circuit Design' ) ), 0, 0, 'Works on biomedical signal processing.' ),
	array( 'Dr. Vineeth Raj', 'assistant_professor', '', 2019, array( 'Communication systems' ), array( array( 'Ph.D.', 'Communication Engineering', 'IIT Kharagpur', 2018 ) ), array( array( 'ECT305', 'Analog and Digital Communication' ) ), 0, 0, 'Research in signal detection for wireless receivers.' ),
	array( 'Prof. Neethu Joseph', 'assistant_professor', '', 2024, array( 'VLSI and micro-nano electronics' ), array( array( 'M.Tech', 'Micro and Nano Electronics', 'College of Engineering Trivandrum', 2022 ) ), array( array( 'ECL331', 'Digital Signal Processing Lab' ) ), 0, 0, 'Works on digital design and FPGA systems.' ),
);
$fid = array();
foreach ( $faculty as $i => $f ) {
	$slug  = strtolower( preg_replace( '/[^a-z]/i', '', explode( ' ', preg_replace( '/^(Dr\.|Prof\.)\s*/', '', $f[0] ) )[0] ) );
	$quals = array();
	foreach ( $f[5] as $q ) {
		$quals[] = array( 'degree' => $q[0], 'specialisation' => $q[1], 'institution' => $q[2], 'year' => $q[3] );
	}
	$courses = array();
	foreach ( $f[6] as $c ) {
		$courses[] = array( 'code' => $c[0], 'name' => $c[1] );
	}
	$id = demo_post( 'faculty', $f[0], array(
		'designation'     => $f[1],
		'additional_role' => $f[2],
		'joined_year'     => $f[3],
		'email'           => $slug . '@cet.ac.in',
		'room'            => 'Room ' . ( 101 + $i ) . ', ECE Block',
		'qualifications'  => $quals,
		'courses'         => $courses,
		'is_guide'        => $f[7],
		'phd_guided'      => $f[8],
		'scholar_url'     => 'https://scholar.google.com/',
	), demo_para( $f[9] ) );
	wp_set_object_terms( $id, demo_terms( $f[4] ), 'research_area' );
	$fid[] = $id;
}

// ---------- Technical staff (invented names) ----------
$staff = array(
	array( 'Rajesh K', 'instructor_grade_1' ), array( 'Sindhu M', 'instructor_grade_2' ),
	array( 'Binu P', 'trade_instructor' ), array( 'Manoj R', 'trade_instructor' ),
	array( 'Ajith Kumar S', 'instrument_mechanic' ), array( 'Sreeja V', 'tradesman' ),
);
$sid = array();
foreach ( $staff as $s ) {
	$sid[] = demo_post( 'staff', $s[0], array( 'staff_category' => $s[1] ) );
}

// ---------- Labs ----------
$teaching = array(
	array( 'Electronic Circuits Lab', 'Hands-on work with amplifiers, oscillators and power supplies.', array( 'btech-ece', 'btech-aei' ), 1, 0, array( array( 'ECL201', 'Scientific Computing Lab', 'B.Tech ECE', 'S3' ), array( 'ECL202', 'Analog Circuits and Simulation Lab', 'B.Tech ECE', 'S4' ) ), "RC coupled amplifier\nWien bridge oscillator\nRegulated power supply\nActive filters\nSchmitt trigger", array( array( 'Digital storage oscilloscope', '100 MHz, 2 channel', 12 ), array( 'Function generator', '20 MHz', 12 ) ), 30 ),
	array( 'Microwave Lab', 'Measurements with microwave benches, antennas and a vector network analyser.', array( 'btech-ece', 'mtech' ), 1, 1, array( array( 'ECL411', 'Electromagnetics Lab', 'B.Tech ECE', 'S7' ) ), "Reflex klystron characteristics\nGunn diode characteristics\nAntenna radiation pattern\nVSWR measurement", array( array( 'Vector network analyser', '6 GHz', 1 ), array( 'X-band microwave bench', 'Klystron and Gunn sources', 6 ) ), 12 ),
	array( 'Fiber Optics Lab', 'Optical sources, detectors and fibre links.', array( 'btech-ece', 'mtech' ), 4, 2, array( array( 'ECL412', 'Optical Communication Lab', 'B.Tech ECE', 'S7' ) ), "Numerical aperture of a fibre\nBending loss\nLED and laser characteristics", array( array( 'Optical power meter', '', 6 ), array( 'Fibre splicing kit', '', 2 ) ), 12 ),
	array( 'Instrumentation and Measurements Lab', 'Transducers, signal conditioning and measurement systems.', array( 'btech-aei' ), 3, 3, array( array( 'AEL201', 'Measurements Lab', 'B.Tech AEI', 'S3' ) ), "Strain gauge characteristics\nLVDT\nThermocouple calibration", array( array( 'Transducer trainer kits', '', 10 ) ), 20 ),
	array( 'Digital Signal Processing Lab', 'DSP algorithms on computers and DSP processors.', array( 'btech-ece' ), 5, 4, array( array( 'ECL331', 'Digital Signal Processing Lab', 'B.Tech ECE', 'S5' ) ), "Linear and circular convolution\nFIR filter design\nFFT on a DSP processor", array( array( 'DSP starter kits', '', 15 ), array( 'Computers', 'With MATLAB and Python', 30 ) ), 30 ),
	array( 'Embedded Systems Lab', 'Microcontrollers, interfacing and embedded software.', array( 'btech-ece', 'btech-aei' ), 8, 5, array( array( 'ECL333', 'Digital Circuits and Embedded Systems Lab', 'B.Tech ECE', 'S5' ) ), "GPIO and timers\nADC and sensor interfacing\nSerial communication", array( array( 'Microcontroller boards', 'ARM Cortex-M', 30 ) ), 30 ),
);
foreach ( $teaching as $l ) {
	$courses = array();
	foreach ( $l[5] as $c ) {
		$courses[] = array( 'code' => $c[0], 'name' => $c[1], 'programme' => $c[2], 'semester' => $c[3] );
	}
	$equip = array();
	foreach ( $l[7] as $e ) {
		$equip[] = array( 'name' => $e[0], 'make_model' => $e[1], 'quantity' => $e[2] );
	}
	$id = demo_post( 'lab', $l[0], array(
		'lab_type'     => 'teaching',
		'summary'      => $l[1],
		'location'     => 'ECE Block',
		'lead_faculty' => $fid[ $l[3] ],
		'tech_staff'   => array( $sid[ $l[4] ] ),
		'workstations' => $l[8],
		'courses'      => $courses,
		'experiments'  => $l[6],
		'equipment'    => $equip,
		'safety_text'  => 'Closed footwear in the lab. No food or drink. Report damaged equipment to the technical staff.',
	), demo_para( $l[1] ) );
	wp_set_object_terms( $id, $l[2], 'programme' );
}

$research = array(
	array( 'Audio Speech and Language Lab', 'Research on speech, music and audio signal processing.', 5, array( 0 ), array( 'Signal and image processing', 'Machine learning' ), 'Low-latency music source separation on embedded devices', 'KSCSTE', 2025, 2028 ),
	array( 'Power Electronics Research Lab', 'Research on power converters, drives and renewable energy systems.', 3, array(), array( 'Control and power electronics' ), 'Grid-tied inverter for rooftop solar', 'CERD', 2024, 2027 ),
	array( 'VLSI Design Lab', 'Research on low-power circuits and hardware accelerators.', 2, array( 8 ), array( 'VLSI and micro-nano electronics' ), 'Energy-efficient hardware for edge AI', 'DST', 2023, 2026 ),
);
foreach ( $research as $r ) {
	$members = array();
	foreach ( $r[3] as $m ) {
		$members[] = $fid[ $m ];
	}
	$id = demo_post( 'lab', $r[0], array(
		'lab_type'       => 'research',
		'summary'        => $r[1],
		'location'       => 'Golden Jubilee PG and Research Block',
		'lead_faculty'   => $fid[ $r[2] ],
		'members'        => $members,
		'scholars'       => array(
			array( 'name' => 'Research scholar A', 'level' => 'phd', 'guide' => $fid[ $r[2] ], 'topic' => '[Thesis topic]', 'status' => 'ongoing' ),
			array( 'name' => 'Research scholar B', 'level' => 'mtech', 'guide' => $fid[ $r[2] ], 'topic' => '[Project topic]', 'status' => 'ongoing' ),
		),
		'projects'       => array(
			array( 'title' => $r[5], 'investigator' => $fid[ $r[2] ], 'agency' => $r[6], 'start_year' => $r[7], 'end_year' => $r[8], 'status' => $r[8] >= 2027 ? 'ongoing' : 'completed' ),
		),
		'equipment'      => array( array( 'name' => 'GPU workstation', 'make_model' => '2 × 24 GB GPUs', 'quantity' => 2 ) ),
		'join_text'      => 'Ph.D. and M.Tech students can write to the lead faculty with a CV and a short statement of interest.',
		'collaborations' => '[Partner institutions or industry]',
	), demo_para( $r[1] ) );
	wp_set_object_terms( $id, array( 'phd', 'mtech' ), 'programme' );
	wp_set_object_terms( $id, demo_terms( $r[4] ), 'research_area' );
}

// ---------- Staff advisor batches ----------
$batches = array(
	array( 'btech-ece', 2026, 'A', 7 ), array( 'btech-ece', 2026, 'B', 8 ),
	array( 'btech-ece', 2025, 'A', 5 ), array( 'btech-ece', 2025, 'B', 6 ),
	array( 'btech-ece', 2024, 'A', 3 ), array( 'btech-ece', 2024, 'B', 4 ),
	array( 'btech-ece', 2023, '', 1 ),
	array( 'btech-aei', 2026, '', 6 ), array( 'btech-aei', 2025, '', 3 ), array( 'btech-aei', 2024, '', 4 ), array( 'btech-aei', 2023, '', 2 ),
	array( 'mtech-sp', 2026, '', 5 ), array( 'mtech-sp', 2025, '', 0 ),
	array( 'mtech-cs', 2026, '', 7 ), array( 'mtech-cs', 2025, '', 1 ),
	array( 'mtech-mne', 2026, '', 8 ), array( 'mtech-mne', 2025, '', 2 ),
	array( 'btech-ece', 2022, '', 1 ), array( 'btech-ece', 2021, '', 2 ), array( 'mtech-sp', 2024, '', 0 ),
);
foreach ( $batches as $b ) {
	$id = demo_post( 'batch', 'Batch', array( 'programme' => $b[0], 'admission_year' => $b[1], 'batch_label' => $b[2], 'advisors' => array( $fid[ $b[3] ] ) ) );
	do_action( 'acf/save_post', $id );
}

// ---------- Publications (invented) ----------
$pubs = array(
	array( 'Learning-based restoration of low-light images', 'A. Varma and A. George', 'IEEE Signal Processing Letters', 'journal', 2026, '33', '', array( 0, 5 ), array( 'Signal and image processing' ) ),
	array( 'Compact antenna arrays for sub-6 GHz receivers', 'T. Mathew and V. Raj', 'IEEE Antennas and Wireless Propagation Letters', 'journal', 2026, '25', '', array( 1, 7 ), array( 'Communication systems' ) ),
	array( 'A low-power accelerator for keyword spotting', 'L. Pillai and N. Joseph', 'Proc. IEEE International Symposium on Circuits and Systems', 'conference', 2026, '', '', array( 2, 8 ), array( 'VLSI and micro-nano electronics' ) ),
	array( 'Real-time music source separation on a Raspberry Pi', 'A. George and A. Varma', 'Proc. IEEE ICASSP', 'conference', 2025, '', '', array( 5, 0 ), array( 'Machine learning' ) ),
	array( 'Fibre Bragg grating sensors for structural monitoring', 'R. Krishnan', 'Optics and Laser Technology', 'journal', 2025, '180', '', array( 4 ), array( 'Optics and photonics' ) ),
	array( 'Model predictive control of a three-level inverter', 'S. Nair', 'Proc. IEEE PEDES', 'conference', 2025, '', '', array( 3 ), array( 'Control and power electronics' ) ),
	array( 'ECG artefact removal with adaptive filters', 'D. S and A. Varma', 'Biomedical Signal Processing and Control', 'journal', 2024, '92', '', array( 6, 0 ), array( 'Biomedical engineering' ) ),
	array( 'Blind detection for MIMO-OFDM receivers', 'V. Raj and T. Mathew', 'Proc. National Conference on Communications', 'conference', 2024, '', '', array( 7, 1 ), array( 'Communication systems' ) ),
);
$pid = array();
foreach ( $pubs as $p ) {
	$authors = array();
	foreach ( $p[7] as $a ) {
		$authors[] = $fid[ $a ];
	}
	$id = demo_post( 'publication', $p[0], array( 'authors' => $p[1], 'venue' => $p[2], 'pub_type' => $p[3], 'year' => $p[4], 'volume' => $p[5], 'faculty' => $authors, 'status' => 'published' ) );
	wp_set_object_terms( $id, demo_terms( $p[8] ), 'research_area' );
	$pid[] = $id;
}
update_field( 'selected_publications', array( $pid[0], $pid[3], $pid[6] ), $fid[0] );
update_field( 'selected_publications', array( $pid[3] ), $fid[5] );

// ---------- News and announcements (from the current site) ----------
function demo_cat( $slug ) {
	$c = get_category_by_slug( $slug );
	return $c ? array( (int) $c->term_id ) : array();
}
$news = array(
	array( 'ROS 2 and TurtleBot 3 workshop', '2026-08-06 10:00:00', 'workshops-and-fdps', '27 participants from several institutions worked hands-on with ROS 2 and TurtleBot 3.' ),
	array( 'CetEcGo science outreach at GHSS Kulathoor', '2025-10-22 10:00:00', 'outreach', 'ECE and AEI students ran science activities for school students.' ),
	array( 'Project Expo by the Department of ECE', '2025-03-25 10:00:00', 'department-news', 'Final-year teams presented their project work.' ),
	array( 'THRIVE: Model Residential School students visit the campus', '2025-01-31 10:00:00', 'outreach', 'Part of a mentoring programme for students of the Model Residential School, Kattela, with 13 ECE and AEI volunteers.' ),
	array( 'Orientation for S5 students', '2024-08-02 10:00:00', 'department-news', 'An orientation session for students entering the fifth semester.' ),
	array( 'Expert talk: Technology trends and opportunities', '2023-08-23 10:00:00', 'talks', 'Shebu Varghese Kuriakose, Director of Technology Management at ARM, UK, spoke to S5 and S7 students.' ),
);
foreach ( $news as $n ) {
	wp_insert_post( array(
		'post_status'   => 'publish',
		'post_title'    => $n[0],
		'post_date'     => $n[1],
		'post_excerpt'  => $n[3],
		'post_category' => demo_cat( $n[2] ),
		'post_content'  => demo_para( $n[3] ) . demo_para( '[Full report, photos and names of coordinators.]' ),
	) );
}
$ann = array(
	array( 'APJAKTU UG examination calendar, Nov 2026 to Feb 2027', '2026-10-15 09:00:00' ),
	array( '[Sample] Internal assessment schedule, S3 and S5', '2026-11-10 09:00:00' ),
	array( '[Sample] Last date for project abstract submission, S7', '2026-11-03 09:00:00' ),
);
foreach ( $ann as $a ) {
	wp_insert_post( array(
		'post_status'   => 'publish',
		'post_title'    => $a[0],
		'post_date'     => $a[1],
		'post_category' => demo_cat( 'announcements' ),
		'post_content'  => demo_para( '[Notice text, with the PDF attached.]' ),
	) );
}

flush_rewrite_rules();
echo 'Demo content ready.';
