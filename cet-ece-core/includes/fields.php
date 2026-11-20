<?php
/**
 * Field groups, defined in code so they are versioned with the plugin.
 * Works with Secure Custom Fields (free) or ACF Pro: both provide repeaters.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

/**
 * Build a field definition. Keys are prefixed with the group so they stay unique.
 */
function cet_ece_f( $group, $name, $label, $type, $extra = array() ) {
	return array_merge( array(
		'key'   => 'field_ece_' . $group . '_' . $name,
		'name'  => $name,
		'label' => $label,
		'type'  => $type,
	), $extra );
}

function cet_ece_when( $group, $field, $value ) {
	return array( array( array( 'field' => 'field_ece_' . $group . '_' . $field, 'operator' => '==', 'value' => $value ) ) );
}

add_action( 'acf/init', function () {
	if ( ! function_exists( 'acf_add_local_field_group' ) ) {
		return;
	}

	$rel_faculty = array( 'post_type' => array( 'faculty' ), 'return_format' => 'id', 'filters' => array( 'search' ) );

	// Faculty.
	acf_add_local_field_group( array(
		'key'      => 'group_ece_faculty',
		'title'    => 'Faculty details',
		'position' => 'acf_after_title',
		'location' => array( array( array( 'param' => 'post_type', 'operator' => '==', 'value' => 'faculty' ) ) ),
		'instruction_placement' => 'field',
		'fields'   => array(
			cet_ece_f( 'fac', 'photo', 'Photo', 'image', array( 'required' => 1, 'return_format' => 'id', 'preview_size' => 'thumbnail', 'mime_types' => 'jpg,jpeg,png,webp', 'instructions' => 'Portrait, plain background. Fill in the Alternative text box in the media window, for example "Photo of Dr. A. Name".' ) ),
			cet_ece_f( 'fac', 'designation', 'Designation', 'select', array( 'required' => 1, 'choices' => cet_ece_designations(), 'instructions' => 'Ad hoc appointments are listed as Assistant Professor.', 'wrapper' => array( 'width' => 50 ) ) ),
			cet_ece_f( 'fac', 'additional_role', 'Additional role', 'text', array( 'instructions' => 'Optional, e.g. Head of Department, Dean.', 'wrapper' => array( 'width' => 50 ) ) ),
			cet_ece_f( 'fac', 'joined_year', 'Joined the department (year)', 'number', array( 'required' => 1, 'min' => 1964, 'max' => 2100, 'wrapper' => array( 'width' => 33 ) ) ),
			cet_ece_f( 'fac', 'email', 'Institutional email', 'email', array( 'required' => 1, 'instructions' => 'Must end in @cet.ac.in.', 'wrapper' => array( 'width' => 33 ) ) ),
			cet_ece_f( 'fac', 'room', 'Room', 'text', array( 'instructions' => 'e.g. Room 214, Golden Jubilee Block.', 'wrapper' => array( 'width' => 34 ) ) ),
			cet_ece_f( 'fac', 'qualifications', 'Qualifications', 'repeater', array(
				'required'     => 1,
				'min'          => 1,
				'layout'       => 'table',
				'button_label' => 'Add qualification',
				'sub_fields'   => array(
					cet_ece_f( 'facq', 'degree', 'Degree', 'text', array( 'required' => 1, 'instructions' => 'e.g. Ph.D., M.Tech, B.Tech' ) ),
					cet_ece_f( 'facq', 'specialisation', 'Specialisation', 'text' ),
					cet_ece_f( 'facq', 'institution', 'Institution', 'text', array( 'required' => 1 ) ),
					cet_ece_f( 'facq', 'year', 'Year', 'number', array( 'min' => 1950, 'max' => 2100 ) ),
				),
			) ),
			cet_ece_f( 'fac', 'scholar_url', 'Google Scholar profile', 'url', array( 'wrapper' => array( 'width' => 33 ) ) ),
			cet_ece_f( 'fac', 'orcid_url', 'ORCID', 'url', array( 'wrapper' => array( 'width' => 33 ) ) ),
			cet_ece_f( 'fac', 'scopus_url', 'Scopus', 'url', array( 'wrapper' => array( 'width' => 34 ) ) ),
			cet_ece_f( 'fac', 'selected_publications', 'Selected publications', 'relationship', array( 'post_type' => array( 'publication' ), 'return_format' => 'id', 'max' => 5, 'filters' => array( 'search' ), 'instructions' => 'Up to five. Add papers first under Publications.' ) ),
			cet_ece_f( 'fac', 'courses', 'Courses taught', 'repeater', array(
				'layout'       => 'table',
				'button_label' => 'Add course',
				'sub_fields'   => array(
					cet_ece_f( 'facc', 'code', 'Course code', 'text' ),
					cet_ece_f( 'facc', 'name', 'Course name', 'text', array( 'required' => 1 ) ),
				),
			) ),
			cet_ece_f( 'fac', 'is_guide', 'Approved Ph.D. guide', 'true_false', array( 'ui' => 1, 'wrapper' => array( 'width' => 33 ) ) ),
			cet_ece_f( 'fac', 'phd_guided', 'Ph.D. scholars guided', 'number', array( 'min' => 0, 'wrapper' => array( 'width' => 33 ) ) ),
			cet_ece_f( 'fac', 'display_order', 'Display order', 'number', array( 'instructions' => 'Optional. Lower numbers appear first within the designation; otherwise sorted by name.', 'wrapper' => array( 'width' => 34 ) ) ),
		),
	) );

	// Labs.
	$research = cet_ece_when( 'lab', 'lab_type', 'research' );
	$teaching = cet_ece_when( 'lab', 'lab_type', 'teaching' );
	acf_add_local_field_group( array(
		'key'      => 'group_ece_lab',
		'title'    => 'Lab details',
		'position' => 'acf_after_title',
		'location' => array( array( array( 'param' => 'post_type', 'operator' => '==', 'value' => 'lab' ) ) ),
		'fields'   => array(
			cet_ece_f( 'lab', 'lab_type', 'Type of lab', 'radio', array( 'required' => 1, 'choices' => array( 'teaching' => 'Teaching lab', 'research' => 'Research lab' ), 'default_value' => 'teaching', 'layout' => 'horizontal' ) ),
			cet_ece_f( 'lab', 'summary', 'Summary', 'textarea', array( 'rows' => 2, 'maxlength' => 240, 'required' => 1, 'instructions' => 'One or two sentences, shown on lab cards and under the page title.' ) ),
			cet_ece_f( 'lab', 'location', 'Location', 'text', array( 'instructions' => 'Block and room.', 'wrapper' => array( 'width' => 50 ) ) ),
			cet_ece_f( 'lab', 'lead_faculty', 'Lab in charge / lead faculty', 'post_object', array_merge( $rel_faculty, array( 'required' => 1, 'wrapper' => array( 'width' => 50 ) ) ) ),
			cet_ece_f( 'lab', 'tech_staff', 'Technical staff', 'relationship', array( 'post_type' => array( 'staff' ), 'return_format' => 'id', 'filters' => array( 'search' ) ) ),
			cet_ece_f( 'lab', 'workstations', 'Workstations', 'number', array( 'min' => 0, 'conditional_logic' => $teaching ) ),
			cet_ece_f( 'lab', 'courses', 'Courses served', 'repeater', array(
				'conditional_logic' => $teaching,
				'layout'            => 'table',
				'button_label'      => 'Add course',
				'sub_fields'        => array(
					cet_ece_f( 'labc', 'code', 'Course code', 'text' ),
					cet_ece_f( 'labc', 'name', 'Course', 'text', array( 'required' => 1 ) ),
					cet_ece_f( 'labc', 'programme', 'Programme', 'text', array( 'instructions' => 'e.g. B.Tech ECE' ) ),
					cet_ece_f( 'labc', 'semester', 'Semester', 'text', array( 'instructions' => 'e.g. S3' ) ),
				),
			) ),
			cet_ece_f( 'lab', 'experiments', 'Experiments', 'textarea', array( 'rows' => 6, 'conditional_logic' => $teaching, 'instructions' => 'One experiment per line.' ) ),
			cet_ece_f( 'lab', 'members', 'Faculty members', 'relationship', array_merge( $rel_faculty, array( 'conditional_logic' => $research ) ) ),
			cet_ece_f( 'lab', 'scholars', 'Research scholars', 'repeater', array(
				'conditional_logic' => $research,
				'layout'            => 'table',
				'button_label'      => 'Add scholar',
				'sub_fields'        => array(
					cet_ece_f( 'labs', 'name', 'Name', 'text', array( 'required' => 1 ) ),
					cet_ece_f( 'labs', 'level', 'Programme', 'select', array( 'choices' => array( 'phd' => 'Ph.D.', 'mtech' => 'M.Tech' ), 'default_value' => 'phd' ) ),
					cet_ece_f( 'labs', 'guide', 'Guide', 'post_object', $rel_faculty ),
					cet_ece_f( 'labs', 'topic', 'Topic', 'text' ),
					cet_ece_f( 'labs', 'status', 'Status', 'select', array( 'choices' => array( 'ongoing' => 'Ongoing', 'completed' => 'Completed' ), 'default_value' => 'ongoing' ) ),
				),
			) ),
			cet_ece_f( 'lab', 'projects', 'Funded projects', 'repeater', array(
				'conditional_logic' => $research,
				'layout'            => 'block',
				'button_label'      => 'Add project',
				'sub_fields'        => array(
					cet_ece_f( 'labp', 'title', 'Project title', 'text', array( 'required' => 1 ) ),
					cet_ece_f( 'labp', 'investigator', 'Principal investigator', 'post_object', array_merge( $rel_faculty, array( 'wrapper' => array( 'width' => 50 ) ) ) ),
					cet_ece_f( 'labp', 'agency', 'Funding agency', 'text', array( 'wrapper' => array( 'width' => 50 ) ) ),
					cet_ece_f( 'labp', 'start_year', 'Start year', 'number', array( 'wrapper' => array( 'width' => 25 ) ) ),
					cet_ece_f( 'labp', 'end_year', 'End year', 'number', array( 'wrapper' => array( 'width' => 25 ) ) ),
					cet_ece_f( 'labp', 'amount', 'Amount (₹ lakh)', 'text', array( 'wrapper' => array( 'width' => 25 ) ) ),
					cet_ece_f( 'labp', 'status', 'Status', 'select', array( 'choices' => array( 'ongoing' => 'Ongoing', 'completed' => 'Completed' ), 'default_value' => 'ongoing', 'wrapper' => array( 'width' => 25 ) ) ),
				),
			) ),
			cet_ece_f( 'lab', 'equipment', 'Major equipment and facilities', 'repeater', array(
				'layout'       => 'table',
				'button_label' => 'Add item',
				'sub_fields'   => array(
					cet_ece_f( 'labe', 'name', 'Item', 'text', array( 'required' => 1 ) ),
					cet_ece_f( 'labe', 'make_model', 'Make and model or details', 'text' ),
					cet_ece_f( 'labe', 'quantity', 'Quantity', 'number', array( 'min' => 0 ) ),
				),
			) ),
			cet_ece_f( 'lab', 'manual', 'Lab manual (PDF)', 'file', array( 'return_format' => 'id', 'mime_types' => 'pdf', 'conditional_logic' => $teaching, 'wrapper' => array( 'width' => 33 ) ) ),
			cet_ece_f( 'lab', 'timetable', 'Lab timetable (PDF)', 'file', array( 'return_format' => 'id', 'mime_types' => 'pdf', 'conditional_logic' => $teaching, 'wrapper' => array( 'width' => 33 ) ) ),
			cet_ece_f( 'lab', 'safety_file', 'Safety rules (PDF)', 'file', array( 'return_format' => 'id', 'mime_types' => 'pdf', 'wrapper' => array( 'width' => 34 ) ) ),
			cet_ece_f( 'lab', 'safety_text', 'Key safety rules', 'textarea', array( 'rows' => 3, 'instructions' => 'Two or three short rules shown on the page.' ) ),
			cet_ece_f( 'lab', 'join_text', 'How to join the lab', 'textarea', array( 'rows' => 3, 'conditional_logic' => $research ) ),
			cet_ece_f( 'lab', 'collaborations', 'Collaborations', 'textarea', array( 'rows' => 2, 'conditional_logic' => $research ) ),
		),
	) );

	// Staff advisor batches.
	$prog_choices = array();
	foreach ( cet_ece_programmes() as $k => $p ) {
		$prog_choices[ $k ] = $p[0];
	}
	acf_add_local_field_group( array(
		'key'      => 'group_ece_batch',
		'title'    => 'Batch',
		'position' => 'acf_after_title',
		'location' => array( array( array( 'param' => 'post_type', 'operator' => '==', 'value' => 'batch' ) ) ),
		'fields'   => array(
			cet_ece_f( 'bat', 'programme', 'Programme', 'select', array( 'required' => 1, 'choices' => $prog_choices, 'wrapper' => array( 'width' => 50 ) ) ),
			cet_ece_f( 'bat', 'admission_year', 'Admission year', 'number', array( 'required' => 1, 'min' => 2000, 'max' => 2100, 'wrapper' => array( 'width' => 25 ) ) ),
			cet_ece_f( 'bat', 'batch_label', 'Batch', 'text', array( 'instructions' => 'A, B… Leave empty for a single batch.', 'wrapper' => array( 'width' => 25 ) ) ),
			cet_ece_f( 'bat', 'advisors', 'Staff advisor(s)', 'relationship', array_merge( $rel_faculty, array( 'required' => 1, 'min' => 1, 'max' => 2 ) ) ),
		),
	) );

	// Publications.
	acf_add_local_field_group( array(
		'key'      => 'group_ece_publication',
		'title'    => 'Publication details',
		'position' => 'acf_after_title',
		'location' => array( array( array( 'param' => 'post_type', 'operator' => '==', 'value' => 'publication' ) ) ),
		'fields'   => array(
			cet_ece_f( 'pub', 'authors', 'Authors', 'text', array( 'required' => 1, 'instructions' => 'As in the paper, IEEE style: A. Kumar, B. Nair, and C. Thomas' ) ),
			cet_ece_f( 'pub', 'venue', 'Journal or conference', 'text', array( 'required' => 1 ) ),
			cet_ece_f( 'pub', 'pub_type', 'Type', 'select', array( 'required' => 1, 'choices' => cet_ece_pub_types(), 'wrapper' => array( 'width' => 25 ) ) ),
			cet_ece_f( 'pub', 'year', 'Year', 'number', array( 'required' => 1, 'min' => 1964, 'max' => 2100, 'wrapper' => array( 'width' => 25 ) ) ),
			cet_ece_f( 'pub', 'volume', 'Volume / issue', 'text', array( 'wrapper' => array( 'width' => 25 ) ) ),
			cet_ece_f( 'pub', 'pages', 'Pages', 'text', array( 'wrapper' => array( 'width' => 25 ) ) ),
			cet_ece_f( 'pub', 'doi', 'DOI', 'text', array( 'instructions' => 'e.g. 10.1109/TASLP.2025.1234567 (a link from doi.org also works).', 'wrapper' => array( 'width' => 50 ) ) ),
			cet_ece_f( 'pub', 'url', 'Link (if no DOI)', 'url', array( 'wrapper' => array( 'width' => 50 ) ) ),
			cet_ece_f( 'pub', 'status', 'Status', 'select', array( 'choices' => array( 'published' => 'Published', 'accepted' => 'Accepted, not yet published' ), 'default_value' => 'published', 'wrapper' => array( 'width' => 50 ) ) ),
			cet_ece_f( 'pub', 'faculty', 'Department authors', 'relationship', array_merge( $rel_faculty, array( 'instructions' => 'Faculty from the department. The paper appears on their profile.' ) ) ),
		),
	) );

	// Technical staff.
	$cats = array();
	foreach ( cet_ece_staff_categories() as $k => $v ) {
		$cats[ $k ] = $v[0];
	}
	acf_add_local_field_group( array(
		'key'      => 'group_ece_staff',
		'title'    => 'Technical staff details',
		'position' => 'acf_after_title',
		'location' => array( array( array( 'param' => 'post_type', 'operator' => '==', 'value' => 'staff' ) ) ),
		'fields'   => array(
			cet_ece_f( 'stf', 'staff_category', 'Designation', 'select', array( 'required' => 1, 'choices' => $cats, 'wrapper' => array( 'width' => 50 ) ) ),
			cet_ece_f( 'stf', 'display_order', 'Display order', 'number', array( 'wrapper' => array( 'width' => 50 ), 'instructions' => 'Optional. Lower numbers first.' ) ),
		),
	) );
} );
