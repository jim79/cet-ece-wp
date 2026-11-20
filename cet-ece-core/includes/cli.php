<?php
/**
 * Importer for the migration from the old site: WP-CLI command and the
 * engine behind Tools > ECE import.
 *
 *   wp ece import faculty      faculty.csv      [--dry-run] [--report=<file>] [--no-photos]
 *   wp ece import staff        staff.csv
 *   wp ece import labs         labs.csv
 *   wp ece import batches      batches.csv
 *   wp ece import publications publications.csv
 *   wp ece import news         news.csv         [--no-photos]
 *
 * Import in this order: faculty, staff, labs, batches, publications, news.
 * Rows are matched by name (titles such as Dr. and Prof. and punctuation are
 * ignored), so running an import again updates entries instead of duplicating them.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

class CET_ECE_Importer {

	private $dry   = false;
	private $log   = array();
	private $index = array();

	public static function types() {
		return array( 'faculty', 'staff', 'labs', 'batches', 'publications', 'news' );
	}

	/**
	 * Run an import and return the log rows (line, action, item, note).
	 * Used by the WP-CLI command and by Tools > ECE import.
	 */
	public function run( $type, $file, $dry = false, $photos = true ) {
		if ( ! function_exists( 'update_field' ) ) {
			throw new Exception( 'Activate Secure Custom Fields first.' );
		}
		if ( ! in_array( $type, self::types(), true ) ) {
			throw new Exception( 'Unknown type. Use ' . implode( ', ', self::types() ) . '.' );
		}
		if ( ! is_readable( $file ) ) {
			throw new Exception( 'Cannot read the CSV file.' );
		}
		$this->dry = $dry;
		$this->log = array();
		require_once ABSPATH . 'wp-admin/includes/media.php';
		require_once ABSPATH . 'wp-admin/includes/file.php';
		require_once ABSPATH . 'wp-admin/includes/image.php';
		$method = 'import_' . $type;
		foreach ( $this->read_csv( $file ) as $n => $row ) {
			$this->$method( $row, $n + 2, $photos );
		}
		return $this->log;
	}

	/* ---------- helpers ---------- */

	private function read_csv( $file ) {
		$fh   = fopen( $file, 'r' );
		$head = fgetcsv( $fh );
		if ( ! $head ) {
			throw new Exception( 'The CSV file is empty.' );
		}
		$head[0] = preg_replace( '/^\xEF\xBB\xBF/', '', $head[0] ); // Excel's byte-order mark.
		$head    = array_map( 'trim', $head );
		$rows    = array();
		while ( ( $r = fgetcsv( $fh ) ) !== false ) {
			if ( count( array_filter( $r, 'strlen' ) ) === 0 ) {
				continue;
			}
			$r      = array_pad( $r, count( $head ), '' );
			$rows[] = array_map( 'trim', array_combine( $head, array_slice( $r, 0, count( $head ) ) ) );
		}
		fclose( $fh );
		return $rows;
	}

	private function note( $line, $action, $item, $note = '' ) {
		$this->log[] = array( 'line' => $line, 'action' => $action, 'item' => $item, 'note' => $note );
	}

	public static function norm( $name ) {
		$n = preg_replace( '/^(dr|prof|mr|ms|mrs|smt|shri)[\.,]?\s+/i', '', trim( (string) $name ) );
		return preg_replace( '/[^a-z]/', '', strtolower( $n ) );
	}

	private function find( $type, $name ) {
		if ( ! isset( $this->index[ $type ] ) ) {
			$this->index[ $type ] = array();
			foreach ( get_posts( array( 'post_type' => $type, 'post_status' => 'any', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true ) ) as $id ) {
				$this->index[ $type ][ self::norm( get_the_title( $id ) ) ] = $id;
			}
		}
		return $this->index[ $type ][ self::norm( $name ) ] ?? 0;
	}

	private function remember( $type, $name, $id ) {
		$this->index[ $type ][ self::norm( $name ) ] = $id;
	}

	private function people( $names, $line, $item ) {
		$ids = array();
		foreach ( array_filter( array_map( 'trim', preg_split( '/[;\n]/', (string) $names ) ) ) as $n ) {
			$id = $this->find( 'faculty', $n );
			if ( $id ) {
				$ids[] = $id;
			} else {
				$this->note( $line, 'warning', $item, "Faculty \"$n\" not found: import faculty first or fix the spelling" );
			}
		}
		return array_values( array_unique( $ids ) );
	}

	private function upsert( $type, $title, $content = null, $extra = array() ) {
		$id = $this->find( $type, $title );
		if ( $this->dry ) {
			return array( $id ? $id : -1, $id ? 'update' : 'create' );
		}
		$data = array_merge( array( 'post_type' => $type, 'post_status' => 'publish', 'post_title' => $title ), $extra );
		if ( null !== $content ) {
			$data['post_content'] = $content;
		}
		if ( $id ) {
			$data['ID'] = $id;
			wp_update_post( $data );
			return array( $id, 'update' );
		}
		$id = wp_insert_post( $data );
		$this->remember( $type, $title, $id );
		return array( $id, 'create' );
	}

	private function set( $id, $fields ) {
		if ( $this->dry || $id < 1 ) {
			return;
		}
		foreach ( $fields as $k => $v ) {
			update_field( $k, $v, $id );
		}
	}

	private function terms( $id, $list, $tax, $create = true ) {
		if ( $this->dry || $id < 1 || '' === trim( (string) $list ) ) {
			return;
		}
		$ids = array();
		foreach ( array_filter( array_map( 'trim', explode( ';', $list ) ) ) as $t ) {
			$term = get_term_by( 'slug', sanitize_title( $t ), $tax );
			if ( ! $term ) {
				$term = get_term_by( 'name', $t, $tax );
			}
			if ( ! $term && $create ) {
				$new  = wp_insert_term( $t, $tax );
				$term = is_wp_error( $new ) ? null : get_term( $new['term_id'], $tax );
			}
			if ( $term ) {
				$ids[] = (int) $term->term_id;
			}
		}
		wp_set_object_terms( $id, $ids, $tax );
	}

	private function sideload( $url, $post_id, $alt ) {
		if ( $this->dry || ! $url || $post_id < 1 ) {
			return 0;
		}
		$att = media_sideload_image( esc_url_raw( $url ), $post_id, $alt, 'id' );
		if ( is_wp_error( $att ) ) {
			return $att;
		}
		update_post_meta( $att, '_wp_attachment_image_alt', $alt );
		return (int) $att;
	}

	/* ---------- importers ---------- */

	private function import_faculty( $r, $line, $photos ) {
		$name = $r['name'] ?? '';
		if ( '' === $name ) {
			return $this->note( $line, 'skipped', '(blank)', 'No name' );
		}
		$keys = array_keys( cet_ece_designations() );
		$des  = $r['designation'] ?? '';
		if ( ! in_array( $des, $keys, true ) ) {
			return $this->note( $line, 'skipped', $name, 'Designation must be one of: ' . implode( ', ', $keys ) );
		}
		$existing = $this->find( 'faculty', $name );
		$content  = null;
		if ( ! $existing && ! empty( $r['specialisation'] ) ) {
			$content = '<!-- wp:paragraph --><p>' . esc_html( 'Specialisation: ' . $r['specialisation'] ) . '</p><!-- /wp:paragraph -->';
		}
		list( $id, $action ) = $this->upsert( 'faculty', $name, $content );
		$fields = array( 'designation' => $des );
		foreach ( array( 'additional_role', 'joined_year', 'email', 'room', 'scholar_url', 'orcid_url', 'scopus_url' ) as $k ) {
			if ( isset( $r[ $k ] ) && '' !== $r[ $k ] ) {
				$fields[ $k ] = $r[ $k ];
			}
		}
		$this->set( $id, $fields );
		$this->terms( $id, $r['research_areas'] ?? '', 'research_area' );
		$note = array();
		if ( ! empty( $r['email'] ) && ! preg_match( '/@cet\.ac\.in$/i', $r['email'] ) ) {
			$note[] = 'personal email: replace with @cet.ac.in';
		}
		if ( $photos && ! empty( $r['photo_url'] ) && ( ! $existing || ! cet_ece_get( 'photo', $id ) ) ) {
			$att = $this->sideload( $r['photo_url'], $id, 'Photo of ' . $name );
			if ( is_wp_error( $att ) ) {
				$note[] = 'photo not downloaded: ' . $att->get_error_message();
			} elseif ( $att ) {
				$this->set( $id, array( 'photo' => $att ) );
			}
		}
		$this->note( $line, $action, $name, implode( '; ', $note ) );
	}

	private function import_staff( $r, $line, $photos ) {
		$name = $r['name'] ?? '';
		$cats = cet_ece_staff_categories();
		$cat  = $r['category'] ?? '';
		if ( ! isset( $cats[ $cat ] ) ) {
			foreach ( $cats as $k => $labels ) {
				if ( 0 === strcasecmp( $cat, $labels[0] ) ) {
					$cat = $k;
				}
			}
		}
		if ( '' === $name || ! isset( $cats[ $cat ] ) ) {
			return $this->note( $line, 'skipped', $name ? $name : '(blank)', 'Needs a name and a category (' . implode( ', ', array_keys( $cats ) ) . ')' );
		}
		list( $id, $action ) = $this->upsert( 'staff', $name );
		$this->set( $id, array( 'staff_category' => $cat ) );
		$note = '';
		if ( ! empty( $r['lab'] ) ) {
			$lab = $this->find( 'lab', $r['lab'] );
			if ( ! $lab ) {
				$note = 'Lab "' . $r['lab'] . '" not found: import labs, then rerun staff';
			} elseif ( ! $this->dry ) {
				$list = cet_ece_ids( cet_ece_get( 'tech_staff', $lab ) );
				if ( ! in_array( $id, $list, true ) ) {
					$list[] = $id;
					update_field( 'tech_staff', $list, $lab );
				}
			}
		}
		$this->note( $line, $action, $name, $note );
	}

	private function import_labs( $r, $line, $photos ) {
		$name = $r['name'] ?? '';
		if ( '' === $name ) {
			return $this->note( $line, 'skipped', '(blank)', 'No name' );
		}
		$type = in_array( $r['type'] ?? '', array( 'teaching', 'research' ), true ) ? $r['type'] : 'teaching';
		list( $id, $action ) = $this->upsert( 'lab', $name );
		$fields = array( 'lab_type' => $type );
		if ( ! empty( $r['summary'] ) ) {
			$fields['summary'] = $r['summary'];
		}
		if ( ! empty( $r['location'] ) ) {
			$fields['location'] = $r['location'];
		}
		$note = array();
		if ( ! empty( $r['lead_faculty'] ) ) {
			$lead = $this->people( $r['lead_faculty'], $line, $name );
			if ( $lead ) {
				$fields['lead_faculty'] = $lead[0];
			}
		} else {
			$note[] = 'no lab in charge yet';
		}
		if ( empty( $r['summary'] ) ) {
			$note[] = 'no summary yet';
		}
		$this->set( $id, $fields );
		$this->terms( $id, $r['programmes'] ?? '', 'programme', false );
		$this->terms( $id, $r['research_areas'] ?? '', 'research_area' );
		$this->note( $line, $action, $name, implode( '; ', $note ) );
	}

	private function import_batches( $r, $line, $photos ) {
		$progs = cet_ece_programmes();
		$prog  = $r['programme'] ?? '';
		$year  = (int) ( $r['admission_year'] ?? 0 );
		$label = strtoupper( trim( $r['batch_label'] ?? '' ) );
		$item  = trim( ( $progs[ $prog ][1] ?? $prog ) . " $year $label" );
		if ( ! isset( $progs[ $prog ] ) || $year < 1990 ) {
			return $this->note( $line, 'skipped', $item, 'Needs a programme (' . implode( ', ', array_keys( $progs ) ) . ') and an admission year' );
		}
		$advisors = $this->people( $r['advisors'] ?? '', $line, $item );
		if ( ! $advisors ) {
			return $this->note( $line, 'skipped', $item, 'No advisor matched an imported faculty member' );
		}
		$existing = 0;
		foreach ( get_posts( array( 'post_type' => 'batch', 'posts_per_page' => -1, 'fields' => 'ids', 'no_found_rows' => true ) ) as $b ) {
			if ( cet_ece_get( 'programme', $b ) === $prog && (int) cet_ece_get( 'admission_year', $b ) === $year && strtoupper( (string) cet_ece_get( 'batch_label', $b ) ) === $label ) {
				$existing = $b;
			}
		}
		if ( $this->dry ) {
			return $this->note( $line, $existing ? 'update' : 'create', $item );
		}
		$id = $existing ? $existing : wp_insert_post( array( 'post_type' => 'batch', 'post_status' => 'publish', 'post_title' => $item ) );
		update_field( 'programme', $prog, $id );
		update_field( 'admission_year', $year, $id );
		update_field( 'batch_label', $label, $id );
		update_field( 'advisors', $advisors, $id );
		do_action( 'acf/save_post', $id );
		$this->note( $line, $existing ? 'update' : 'create', $item, cet_ece_batch_is_current( $prog, $year ) ? '' : 'graduated: shows under past batches' );
	}

	private function import_publications( $r, $line, $photos ) {
		$title = $r['title'] ?? '';
		if ( '' === $title || '' === ( $r['year'] ?? '' ) ) {
			return $this->note( $line, 'skipped', $title ? $title : substr( $r['raw'] ?? '', 0, 60 ), 'Needs at least a title and a year' );
		}
		$types = array_keys( cet_ece_pub_types() );
		list( $id, $action ) = $this->upsert( 'publication', $title );
		$doi = preg_replace( '#^(https?://)?(dx\.)?doi\.org/#i', '', trim( $r['doi'] ?? '' ) );
		$note = array();
		if ( $doi && ! preg_match( '#^10\.\d{4,9}/\S+$#', $doi ) ) {
			$note[] = "DOI \"$doi\" is not valid and was left out";
			$doi    = '';
		}
		$this->set( $id, array(
			'authors'  => $r['authors'] ?? '',
			'venue'    => $r['venue'] ?? '',
			'pub_type' => in_array( $r['type'] ?? '', $types, true ) ? $r['type'] : 'other',
			'year'     => (int) $r['year'],
			'volume'   => $r['volume'] ?? '',
			'pages'    => $r['pages'] ?? '',
			'doi'      => $doi,
			'url'      => $r['url'] ?? '',
			'status'   => 'accepted' === ( $r['status'] ?? '' ) ? 'accepted' : 'published',
		) );
		$fac = $this->people( $r['faculty'] ?? '', $line, $title );
		if ( $fac ) {
			$this->set( $id, array( 'faculty' => $fac ) );
		}
		$this->terms( $id, $r['research_areas'] ?? '', 'research_area' );
		if ( ( $r['confidence'] ?? '' ) === 'low' ) {
			$note[] = 'parsed with low confidence: check authors and venue';
		}
		$this->note( $line, $action, $title, implode( '; ', $note ) );
	}

	private function import_news( $r, $line, $photos ) {
		$title = $r['title'] ?? '';
		$date  = $r['date'] ?? '';
		if ( '' === $title ) {
			return $this->note( $line, 'skipped', '(blank)', 'No title' );
		}
		$dupe = get_posts( array( 'post_type' => 'post', 'title' => $title, 'post_status' => 'any', 'fields' => 'ids', 'posts_per_page' => 1, 'no_found_rows' => true ) );
		if ( $dupe ) {
			return $this->note( $line, 'skipped', $title, 'Already imported' );
		}
		$cat = get_category_by_slug( $r['category'] ?? '' );
		if ( ! $cat ) {
			$cat = get_category_by_slug( 'department-news' );
		}
		if ( $this->dry ) {
			return $this->note( $line, 'create', $title, $cat ? $cat->name : '' );
		}
		$content = (string) ( $r['content_html'] ?? '' );
		if ( '' !== $content && false === strpos( $content, '<!-- wp:' ) ) {
			$content = "<!-- wp:html -->\n" . $content . "\n<!-- /wp:html -->";
		}
		$id = wp_insert_post( array(
			'post_type'     => 'post',
			'post_status'   => 'publish',
			'post_title'    => $title,
			'post_name'     => $r['slug'] ?? '',
			'post_date'     => $date ? $date : current_time( 'mysql' ),
			'post_excerpt'  => $r['excerpt'] ?? '',
			'post_content'  => $content,
			'post_category' => $cat ? array( $cat->term_id ) : array(),
		) );
		$note = $cat ? $cat->name : '';
		if ( $photos && ! empty( $r['featured_image_url'] ) ) {
			$att = $this->sideload( $r['featured_image_url'], $id, $title );
			if ( is_wp_error( $att ) ) {
				$note .= '; image not downloaded: ' . $att->get_error_message();
			} elseif ( $att ) {
				set_post_thumbnail( $id, $att );
			}
		}
		$this->note( $line, 'create', $title, $note );
	}
}

if ( defined( 'WP_CLI' ) && WP_CLI ) {

	class CET_ECE_Import_Command {

		/**
		 * Import a CSV made by tools/migrate/convert_old_site.py (after review).
		 *
		 * ## OPTIONS
		 *
		 * <type>
		 * : faculty, staff, labs, batches, publications or news.
		 *
		 * <file>
		 * : Path to the CSV file.
		 *
		 * [--dry-run]
		 * : Show what would happen without changing anything.
		 *
		 * [--report=<file>]
		 * : Also write the results to this CSV file.
		 *
		 * [--no-photos]
		 * : Do not download photos and images.
		 *
		 * ## EXAMPLES
		 *
		 *     wp ece import faculty migration/faculty.csv --dry-run
		 *     wp ece import faculty migration/faculty.csv --report=faculty-report.csv
		 *
		 * @when after_wp_load
		 */
		public function import( $args, $assoc ) {
			list( $type, $file ) = $args;
			$dry = isset( $assoc['dry-run'] );
			try {
				$log = ( new CET_ECE_Importer() )->run( $type, $file, $dry, ! isset( $assoc['no-photos'] ) );
			} catch ( Exception $e ) {
				WP_CLI::error( $e->getMessage() );
			}
			WP_CLI\Utils\format_items( 'table', $log, array( 'line', 'action', 'item', 'note' ) );
			$counts = array_count_values( wp_list_pluck( $log, 'action' ) );
			ksort( $counts );
			WP_CLI::log( '' );
			foreach ( $counts as $k => $v ) {
				WP_CLI::log( sprintf( '%-10s %d', $k, $v ) );
			}
			if ( ! empty( $assoc['report'] ) ) {
				$fh = fopen( $assoc['report'], 'w' );
				fputcsv( $fh, array( 'line', 'action', 'item', 'note' ) );
				foreach ( $log as $l ) {
					fputcsv( $fh, $l );
				}
				fclose( $fh );
				WP_CLI::log( 'Report written to ' . $assoc['report'] );
			}
			$dry ? WP_CLI::warning( 'Dry run: nothing was changed.' ) : WP_CLI::success( 'Import finished.' );
		}
	}

	WP_CLI::add_command( 'ece', 'CET_ECE_Import_Command' );
}
