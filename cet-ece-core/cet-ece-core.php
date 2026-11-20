<?php
/**
 * Plugin Name:       CET ECE Core
 * Description:       Content types, fields and blocks for the ECE department website: Faculty, Labs, Staff advisor batches, Publications and Technical staff. Needs Secure Custom Fields (free) or ACF Pro.
 * Version:           1.0.0
 * Requires at least: 6.8
 * Requires PHP:      8.0
 * Author:            Department of ECE, College of Engineering Trivandrum
 * License:           GPL-2.0-or-later
 * Text Domain:       cet-ece-core
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

define( 'CET_ECE_CORE_VERSION', '1.0.0' );
define( 'CET_ECE_CORE_DIR', plugin_dir_path( __FILE__ ) );
define( 'CET_ECE_CORE_URL', plugin_dir_url( __FILE__ ) );

require_once CET_ECE_CORE_DIR . 'includes/helpers.php';
require_once CET_ECE_CORE_DIR . 'includes/content-types.php';
require_once CET_ECE_CORE_DIR . 'includes/fields.php';
require_once CET_ECE_CORE_DIR . 'includes/validation.php';
require_once CET_ECE_CORE_DIR . 'includes/render.php';
require_once CET_ECE_CORE_DIR . 'includes/news.php';
require_once CET_ECE_CORE_DIR . 'includes/blocks.php';
require_once CET_ECE_CORE_DIR . 'includes/bibtex.php';
require_once CET_ECE_CORE_DIR . 'includes/hardening.php';
require_once CET_ECE_CORE_DIR . 'includes/redirects.php';
require_once CET_ECE_CORE_DIR . 'includes/seo.php';
require_once CET_ECE_CORE_DIR . 'includes/cli.php';
require_once CET_ECE_CORE_DIR . 'includes/import-screen.php';

register_activation_hook( __FILE__, function () {
	cet_ece_register_content_types();
	cet_ece_seed_terms();
	flush_rewrite_rules();
} );

register_deactivation_hook( __FILE__, 'flush_rewrite_rules' );

/**
 * Warn administrators when no custom-fields plugin is active.
 */
add_action( 'admin_notices', function () {
	if ( function_exists( 'acf_add_local_field_group' ) || ! current_user_can( 'activate_plugins' ) ) {
		return;
	}
	echo '<div class="notice notice-error"><p><strong>CET ECE Core:</strong> install and activate <em>Secure Custom Fields</em> (Plugins &rsaquo; Add New, free) so the Faculty, Lab and Publication forms appear.</p></div>';
} );
