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
 *   wp ece import sections     sections.csv
 *
 * Import in this order: faculty, staff, labs, batches, publications, news, sections.
 * Photos, lab manuals, syllabus PDFs and images in news posts are copied from
 * the old site into the media library, and links to them are rewritten.
 * Rows are matched by name (titles such as Dr. and Prof. and punctuation are
 * ignored), so running an import again updates entries instead of duplicating them.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

class CET_ECE_Importer {

	private $dry    = false;
	private $log    = array();
	private $index  = array();
	private $photos = true;

	/** Address of the old site: links to its uploads are copied into the media library. */
	const OLD_HOST = 'ece.cet.ac.in';

	public static function types() {
		return array( 'faculty', 'staff', 'labs', 'batches', 'publications', 'news', 'sections' );
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
		$this->dry    = $dry;
		$this->log    = array();
		$this->photos = $photos;
		@set_time_limit( 0 ); // phpcs:ignore WordPress.PHP.NoSilencedErrors -- downloads take a while.
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
		$n = preg_replace( '/^(dr|prof|mr|ms|mrs|smt|shri)\b[\W_]*/i', '', trim( (string) $name ) );
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
		$att = $this->media( $url, $post_id, $alt );
		return $att;
	}

	/**
	 * Copy a file into the media library, once: later imports reuse it.
	 * Returns the attachment ID or a WP_Error.
	 */
	private function media( $url, $post_id = 0, $alt = '' ) {
		$url = esc_url_raw( trim( $url ) );
		if ( ! $url ) {
			return new WP_Error( 'ece_url', 'No address' );
		}
		// The old site links to its files over both http and https: one copy each.
		$url = preg_replace( '#^http://(www\.)?' . preg_quote( self::OLD_HOST, '#' ) . '/#i', 'https://' . self::OLD_HOST . '/', $url );
		$found = get_posts( array( 'post_type' => 'attachment', 'post_status' => 'inherit', 'meta_key' => '_ece_source_url', 'meta_value' => $url, 'fields' => 'ids', 'posts_per_page' => 1, 'no_found_rows' => true ) ); // phpcs:ignore WordPress.DB.SlowDBQuery
		if ( $found ) {
			return (int) $found[0];
		}
		$tmp = download_url( $url, 120 );
		if ( is_wp_error( $tmp ) ) {
			return $tmp;
		}
		$name = sanitize_file_name( rawurldecode( basename( wp_parse_url( $url, PHP_URL_PATH ) ) ) );
		$att  = media_handle_sideload( array( 'name' => $name, 'tmp_name' => $tmp ), $post_id );
		if ( is_wp_error( $att ) ) {
			@unlink( $tmp ); // phpcs:ignore WordPress.PHP.NoSilencedErrors
			return $att;
		}
		update_post_meta( $att, '_ece_source_url', $url );
		if ( $alt && wp_attachment_is_image( $att ) ) {
			update_post_meta( $att, '_wp_attachment_image_alt', $alt );
		}
		return (int) $att;
	}

	/**
	 * Point links and images at copies in this site's media library.
	 * $notes collects files that could not be copied.
	 */
	private function localise( $html, $post_id, &$notes ) {
		if ( ! $this->photos || $this->dry ) {
			return $html;
		}
		$html = preg_replace( '/\s(srcset|sizes)="[^"]*"/i', '', $html );
		return preg_replace_callback( '#https?://(?:www\.)?' . preg_quote( self::OLD_HOST, '#' ) . '/wp-content/uploads/[^"\'\s<>()]+#i', function ( $m ) use ( $post_id, &$notes ) {
			$url = html_entity_decode( $m[0] );
			// A resized copy ("photo-1024x768.jpg"): take the original.
			$url = preg_replace( '/-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp|gif)$)/i', '', $url );
			$url = preg_replace( '#^http://#i', 'https://', $url );
			$att = $this->media( $url, $post_id );
			if ( is_wp_error( $att ) ) {
				$notes[] = 'not copied: ' . basename( $url ) . ' (' . $att->get_error_message() . ')';
				return $m[0];
			}
			return esc_url( wp_get_attachment_url( $att ) );
		}, $html );
	}

	/* ---------- the review markup used in the CSVs ---------- */

	private static function inline( $text ) {
		$text = esc_html( $text );
		// [label](https://...) and [label](/path/) and [label](mailto:...)
		return preg_replace_callback( '/\[([^\]]+)\]\(((?:https?:\/\/|\/|mailto:)[^)\s]+)\)/', function ( $m ) {
			return '<a href="' . esc_url( html_entity_decode( $m[2] ) ) . '">' . $m[1] . '</a>';
		}, $text );
	}

	/**
	 * Turn the review markup into blocks: "## " headings (shifted down by
	 * $shift levels), "- " bullets, "1. " numbered items, "| a | b |" tables
	 * (first row is the header), blank lines between paragraphs.
	 */
	public static function markup_to_blocks( $text, $shift = 0 ) {
		$out   = array();
		$para  = array();
		$list  = array();
		$ltype = '';
		$table = array();
		$flush = function () use ( &$out, &$para, &$list, &$ltype, &$table ) {
			if ( $para ) {
				$out[] = "<!-- wp:paragraph -->\n<p>" . implode( '<br>', $para ) . "</p>\n<!-- /wp:paragraph -->";
				$para  = array();
			}
			if ( $list ) {
				$items = '';
				foreach ( $list as $li ) {
					$items .= "<!-- wp:list-item -->\n<li>" . $li . "</li>\n<!-- /wp:list-item -->";
				}
				$out[] = 'ol' === $ltype
					? "<!-- wp:list {\"ordered\":true} -->\n<ol class=\"wp-block-list\">" . $items . "</ol>\n<!-- /wp:list -->"
					: "<!-- wp:list -->\n<ul class=\"wp-block-list\">" . $items . "</ul>\n<!-- /wp:list -->";
				$list  = array();
				$ltype = '';
			}
			if ( $table ) {
				$head = array_shift( $table );
				$h    = '<thead><tr>';
				foreach ( $head as $c ) {
					$h .= '<th>' . $c . '</th>';
				}
				$h .= '</tr></thead><tbody>';
				foreach ( $table as $r ) {
					$h .= '<tr>';
					foreach ( $r as $c ) {
						$h .= '<td>' . $c . '</td>';
					}
					$h .= '</tr>';
				}
				$out[] = "<!-- wp:table {\"hasFixedLayout\":false} -->\n<figure class=\"wp-block-table\"><table>" . $h . "</tbody></table></figure>\n<!-- /wp:table -->";
				$table = array();
			}
		};
		foreach ( preg_split( '/\r\n|\r|\n/', (string) $text ) as $line ) {
			$line = rtrim( $line );
			if ( '' === trim( $line ) ) {
				$flush();
				continue;
			}
			if ( preg_match( '/^(#{2,4})\s+(.+)$/', $line, $m ) ) {
				$flush();
				$level = min( 6, strlen( $m[1] ) + $shift );
				$attrs = 2 === $level ? '' : ' {"level":' . $level . '}';
				$out[] = '<!-- wp:heading' . $attrs . " -->\n<h$level class=\"wp-block-heading\">" . self::inline( $m[2] ) . "</h$level>\n<!-- /wp:heading -->";
				continue;
			}
			if ( preg_match( '/^\|(.+)\|$/', $line, $m ) ) {
				if ( $para || $list ) {
					$tmp   = $table;
					$table = array();
					$flush();
					$table = $tmp;
				}
				$table[] = array_map( function ( $c ) {
					return self::inline( trim( $c ) );
				}, explode( '|', $m[1] ) );
				continue;
			}
			$type = '';
			if ( preg_match( '/^[-*•]\s+(.+)$/u', $line, $m ) ) {
				$type = 'ul';
			} elseif ( preg_match( '/^\d{1,3}[.)]\s+(.+)$/', $line, $m ) ) {
				$type = 'ol';
			}
			if ( $type ) {
				if ( $para || $table || ( $list && $ltype !== $type ) ) {
					$flush();
				}
				$ltype  = $type;
				$list[] = self::inline( $m[1] );
				continue;
			}
			if ( $list || $table ) {
				$flush();
			}
			$para[] = self::inline( $line );
		}
		$flush();
		return implode( "\n\n", $out );
	}

	/** "a | b | c" lines -> arrays of trimmed cells. */
	private static function rows( $text ) {
		$out = array();
		foreach ( preg_split( '/\r\n|\r|\n/', (string) $text ) as $line ) {
			if ( '' !== trim( $line ) ) {
				$out[] = array_map( 'trim', explode( '|', $line ) );
			}
		}
		return $out;
	}

	/**
	 * Replace the body of an entry with imported content, unless someone has
	 * edited it on the new site since the last import.
	 */
	private function set_content( $id, $content, &$note ) {
		if ( $this->dry || $id < 1 || '' === trim( $content ) ) {
			return;
		}
		$current = (string) get_post_field( 'post_content', $id );
		$last    = (string) get_post_meta( $id, '_ece_imported_hash', true );
		$stub = 0 === strpos( $current, '<!-- wp:paragraph --><p>Specialisation:' ); // written by earlier imports
		if ( '' !== trim( $current ) && ! $stub && md5( $current ) !== $last ) {
			$note[] = 'text edited on this site since the last import: kept';
			return;
		}
		wp_update_post( array( 'ID' => $id, 'post_content' => wp_slash( $content ) ) );
		update_post_meta( $id, '_ece_imported_hash', md5( (string) get_post_field( 'post_content', $id ) ) );
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
		$quals  = array();
		foreach ( self::rows( $r['qualifications'] ?? '' ) as $q ) {
			if ( '' !== ( $q[0] ?? '' ) ) {
				$quals[] = array( 'degree' => $q[0], 'specialisation' => $q[1] ?? '', 'institution' => $q[2] ?? '', 'year' => preg_match( '/^\d{4}$/', $q[3] ?? '' ) ? (int) $q[3] : '' );
			}
		}
		if ( $quals ) {
			$fields['qualifications'] = $quals;
		}
		$courses = array();
		foreach ( self::rows( $r['courses'] ?? '' ) as $c ) {
			$courses[] = count( $c ) > 1 ? array( 'code' => $c[0], 'name' => $c[1] ) : array( 'code' => '', 'name' => $c[0] );
		}
		if ( $courses ) {
			$fields['courses'] = $courses;
		}
		if ( isset( $r['is_guide'] ) && '' !== $r['is_guide'] ) {
			$fields['is_guide'] = in_array( strtolower( $r['is_guide'] ), array( '1', 'yes', 'true', 'y' ), true ) ? 1 : 0;
		}
		foreach ( array( 'additional_role', 'joined_year', 'email', 'room', 'scholar_url', 'orcid_url', 'scopus_url' ) as $k ) {
			if ( isset( $r[ $k ] ) && '' !== $r[ $k ] ) {
				$fields[ $k ] = $r[ $k ];
			}
		}
		$this->set( $id, $fields );
		$this->terms( $id, $r['research_areas'] ?? '', 'research_area' );
		$note = array();
		if ( ! empty( $r['about'] ) ) {
			$this->set_content( $id, $this->localise( self::markup_to_blocks( $r['about'], 1 ), $id, $note ), $note );
		}
		if ( ! $quals ) {
			$note[] = 'no qualifications yet';
		}
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
				$note = 'Lab "' . $r['lab'] . '" not imported yet: the labs import links staff to their labs';
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
		foreach ( array( 'summary', 'location' ) as $k ) {
			if ( ! empty( $r[ $k ] ) ) {
				$fields[ $k ] = 'summary' === $k ? mb_substr( $r[ $k ], 0, 240 ) : $r[ $k ];
			}
		}
		$note = array();
		if ( ! empty( $r['lead_faculty'] ) ) {
			$lead = $this->people( $r['lead_faculty'], $line, $name );
			if ( $lead ) {
				$fields['lead_faculty'] = $lead[0];
				if ( 'research' === $type && count( $lead ) > 1 ) {
					$fields['members'] = array_slice( $lead, 1 );
				}
			}
		} else {
			$note[] = 'no lab in charge yet';
		}
		if ( ! empty( $r['tech_staff'] ) ) {
			$staff = array();
			foreach ( array_filter( array_map( 'trim', explode( ';', $r['tech_staff'] ) ) ) as $n ) {
				$sid = $this->find( 'staff', $n );
				if ( $sid ) {
					$staff[] = $sid;
				} else {
					$note[] = "technical staff \"$n\" not found: import staff first";
				}
			}
			if ( $staff ) {
				$fields['tech_staff'] = $staff;
			}
		}
		$courses = array();
		foreach ( self::rows( $r['courses'] ?? '' ) as $c ) {
			if ( '' !== ( $c[1] ?? '' ) ) {
				$courses[] = array( 'code' => $c[0], 'name' => $c[1], 'programme' => $c[2] ?? '', 'semester' => $c[3] ?? '' );
			}
		}
		if ( $courses ) {
			$fields['courses'] = $courses;
		}
		$scholars = array();
		foreach ( self::rows( $r['scholars'] ?? '' ) as $sc ) {
			if ( '' === ( $sc[0] ?? '' ) ) {
				continue;
			}
			$guide      = ! empty( $sc[2] ) ? $this->find( 'faculty', $sc[2] ) : 0;
			$scholars[] = array(
				'name'   => $sc[0],
				'level'  => 'mtech' === ( $sc[1] ?? '' ) ? 'mtech' : 'phd',
				'guide'  => $guide ? $guide : '',
				'topic'  => $sc[3] ?? '',
				'status' => 'completed' === ( $sc[4] ?? '' ) ? 'completed' : 'ongoing',
			);
		}
		if ( $scholars ) {
			$fields['scholars'] = $scholars;
		}
		if ( empty( $r['summary'] ) ) {
			$note[] = 'no summary yet';
		}
		$this->set( $id, $fields );
		$this->terms( $id, $r['programmes'] ?? '', 'programme', false );
		$this->terms( $id, $r['research_areas'] ?? '', 'research_area' );

		if ( ! $this->dry && $id > 0 ) {
			$content = self::markup_to_blocks( $r['content'] ?? '' );
			if ( $photos ) {
				$gallery = '';
				foreach ( array_filter( array_map( 'trim', preg_split( '/\r\n|\r|\n/', (string) ( $r['gallery'] ?? '' ) ) ) ) as $k => $u ) {
					$att = $this->media( $u, $id, 'Photo of the ' . $name );
					if ( is_wp_error( $att ) ) {
						$note[] = 'photo not copied: ' . $att->get_error_message();
						continue;
					}
					$src      = esc_url( wp_get_attachment_image_url( $att, 'large' ) );
					$gallery .= '<!-- wp:image {"id":' . $att . ',"sizeSlug":"large","linkDestination":"none"} -->' . "\n" . '<figure class="wp-block-image size-large"><img src="' . $src . '" alt="' . esc_attr( 'Photo of the ' . $name ) . '" class="wp-image-' . $att . '"/></figure>' . "\n<!-- /wp:image -->\n\n";
				}
				if ( $gallery ) {
					$content .= "\n\n<!-- wp:heading -->\n<h2 class=\"wp-block-heading\">Photos</h2>\n<!-- /wp:heading -->\n\n<!-- wp:gallery {\"linkTo\":\"none\"} -->\n<figure class=\"wp-block-gallery has-nested-images columns-default is-cropped\">" . $gallery . "</figure>\n<!-- /wp:gallery -->";
				}
				if ( ! empty( $r['photo_url'] ) && ! get_post_thumbnail_id( $id ) ) {
					$att = $this->media( $r['photo_url'], $id, 'Photo of the ' . $name );
					if ( is_wp_error( $att ) ) {
						$note[] = 'photo not copied: ' . $att->get_error_message();
					} else {
						set_post_thumbnail( $id, $att );
					}
				}
				if ( ! empty( $r['manual_url'] ) && ! cet_ece_get( 'manual', $id ) ) {
					$att = $this->media( $r['manual_url'], $id );
					if ( is_wp_error( $att ) ) {
						$note[] = 'lab manual not copied: ' . $att->get_error_message();
					} else {
						update_field( 'manual', $att, $id );
					}
				}
			}
			$this->set_content( $id, $this->localise( $content, $id, $note ), $note );
		}
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
			// A run that stopped part-way: finish copying the pictures of posts already in.
			$old = (string) get_post_field( 'post_content', $dupe[0] );
			if ( $photos && ! $this->dry && false !== stripos( $old, self::OLD_HOST ) ) {
				$notes = array();
				$local = $this->localise( $old, $dupe[0], $notes );
				if ( $local !== $old ) {
					wp_update_post( array( 'ID' => $dupe[0], 'post_content' => wp_slash( $local ) ) );
					return $this->note( $line, 'update', $title, 'Already imported; pictures copied' . ( $notes ? ': ' . implode( '; ', $notes ) : '' ) );
				}
			}
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
		$notes   = array();
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
			'post_content'  => wp_slash( $content ),
			'post_category' => $cat ? array( $cat->term_id ) : array(),
		) );
		if ( $photos && false !== stripos( $content, self::OLD_HOST ) ) {
			$local = $this->localise( $content, $id, $notes );
			if ( $local !== $content ) {
				wp_update_post( array( 'ID' => $id, 'post_content' => wp_slash( $local ) ) );
			}
		}
		$note = $cat ? $cat->name : '';
		if ( $notes ) {
			$note .= '; ' . implode( '; ', array_slice( $notes, 0, 3 ) ) . ( count( $notes ) > 3 ? '; and ' . ( count( $notes ) - 3 ) . ' more' : '' );
		}
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

	/**
	 * Department pages: replace the blocks under a heading, add a section, or
	 * replace a placeholder such as "[Faculty name]".
	 */
	private function import_sections( $r, $line, $photos ) {
		$path   = trim( $r['page'] ?? '', '/ ' );
		$action = $r['action'] ?? '';
		$target = $r['target'] ?? '';
		$item   = $path . ' › ' . $target;
		$page   = $path ? get_page_by_path( $path ) : null;
		if ( ! $page ) {
			return $this->note( $line, 'skipped', $item, 'Page /' . $path . '/ not found' );
		}
		if ( ! in_array( $action, array( 'replace_section', 'add_section', 'replace_text' ), true ) || '' === $target ) {
			return $this->note( $line, 'skipped', $item, 'Needs an action (replace_section, add_section or replace_text) and a target' );
		}
		$html = (string) $page->post_content;
		$note = array();
		if ( 'replace_text' === $action ) {
			$count = substr_count( $html, $target );
			if ( ! $count ) {
				return $this->note( $line, 'unchanged', $item, 'Text not on the page (already replaced?)' );
			}
			$new = str_replace( $target, esc_html( $r['content'] ?? '' ), $html );
		} else {
			$body   = $this->dry ? '' : $this->localise( self::markup_to_blocks( $r['content'] ?? '' ), $page->ID, $note );
			$blocks = parse_blocks( $html );
			$start  = -1;
			$level  = 2;
			foreach ( $blocks as $i => $b ) {
				if ( 'core/heading' === $b['blockName'] && 0 === strcasecmp( trim( wp_strip_all_tags( $b['innerHTML'] ) ), trim( $target ) ) ) {
					$start = $i;
					$level = (int) ( $b['attrs']['level'] ?? 2 );
					break;
				}
			}
			$section = parse_blocks( $body );
			if ( $start < 0 ) {
				if ( 'replace_section' === $action ) {
					$note[] = 'heading not found: added at the end';
				}
				$heading = parse_blocks( "<!-- wp:heading -->\n<h2 class=\"wp-block-heading\">" . esc_html( $target ) . "</h2>\n<!-- /wp:heading -->" );
				$blocks  = array_merge( $blocks, $heading, $section );
			} else {
				$end = count( $blocks );
				for ( $j = $start + 1; $j < count( $blocks ); $j++ ) {
					if ( 'core/heading' === $blocks[ $j ]['blockName'] && (int) ( $blocks[ $j ]['attrs']['level'] ?? 2 ) <= $level ) {
						$end = $j;
						break;
					}
				}
				array_splice( $blocks, $start + 1, $end - $start - 1, $section );
			}
			$new = serialize_blocks( $blocks );
		}
		if ( ! $this->dry ) {
			if ( ! get_post_meta( $page->ID, '_ece_before_import', true ) ) {
				update_post_meta( $page->ID, '_ece_before_import', wp_slash( $html ) ); // one copy of the starter text, for comparison
			}
			wp_update_post( array( 'ID' => $page->ID, 'post_content' => wp_slash( $new ) ) );
		}
		$this->note( $line, 'update', $item, implode( '; ', $note ) );
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
		 * : faculty, staff, labs, batches, publications, news or sections.
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
