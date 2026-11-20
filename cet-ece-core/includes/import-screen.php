<?php
/**
 * Tools > ECE import: upload a reviewed CSV and import it, without the command line.
 *
 * @package cet-ece-core
 */

defined( 'ABSPATH' ) || exit;

add_action( 'admin_menu', function () {
	add_management_page( 'ECE import', 'ECE import', 'manage_options', 'cet-ece-import', 'cet_ece_import_screen' );
} );

function cet_ece_import_screen() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( 'Not allowed.' );
	}
	$labels = array(
		'faculty'      => 'Faculty',
		'staff'        => 'Technical staff',
		'labs'         => 'Labs',
		'batches'      => 'Staff advisor batches',
		'publications' => 'Publications',
		'news'         => 'News and announcements',
	);
	$log   = null;
	$error = '';
	$type  = '';
	$dry   = true;

	if ( isset( $_POST['cet_ece_import_nonce'] ) && wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['cet_ece_import_nonce'] ) ), 'cet_ece_import' ) ) {
		$type = sanitize_key( wp_unslash( $_POST['type'] ?? '' ) );
		$dry  = ! empty( $_POST['dry_run'] );
		$file = $_FILES['csv'] ?? null; // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
		if ( ! $file || UPLOAD_ERR_OK !== $file['error'] || ! is_uploaded_file( $file['tmp_name'] ) ) {
			$error = 'Choose a CSV file to upload.';
		} elseif ( ! preg_match( '/\.csv$/i', $file['name'] ) ) {
			$error = 'The file must be a .csv file. In Excel or Google Sheets, use File › Download › CSV.';
		} else {
			@set_time_limit( 600 ); // phpcs:ignore WordPress.PHP.NoSilencedErrors
			try {
				$log = ( new CET_ECE_Importer() )->run( $type, $file['tmp_name'], $dry, empty( $_POST['no_photos'] ) );
			} catch ( Exception $e ) {
				$error = $e->getMessage();
			}
		}
	}
	?>
	<div class="wrap">
		<h1>ECE import</h1>
		<p>Load a reviewed spreadsheet from the old website. Save it as CSV first. Import in this order: Faculty, Technical staff, Labs, Staff advisor batches, Publications, News.</p>
		<p>Entries are matched by name, so importing the same file again updates entries instead of adding duplicates. Run a <strong>dry run</strong> first: it shows what would happen and changes nothing.</p>

		<?php if ( $error ) : ?>
			<div class="notice notice-error"><p><?php echo esc_html( $error ); ?></p></div>
		<?php endif; ?>

		<form method="post" enctype="multipart/form-data">
			<?php wp_nonce_field( 'cet_ece_import', 'cet_ece_import_nonce' ); ?>
			<table class="form-table" role="presentation">
				<tr>
					<th scope="row"><label for="type">What to import</label></th>
					<td><select name="type" id="type">
						<?php foreach ( $labels as $k => $v ) : ?>
							<option value="<?php echo esc_attr( $k ); ?>" <?php selected( $type, $k ); ?>><?php echo esc_html( $v ); ?></option>
						<?php endforeach; ?>
					</select></td>
				</tr>
				<tr>
					<th scope="row"><label for="csv">CSV file</label></th>
					<td><input type="file" name="csv" id="csv" accept=".csv,text/csv" required></td>
				</tr>
				<tr>
					<th scope="row">Options</th>
					<td>
						<label><input type="checkbox" name="dry_run" value="1" <?php checked( $dry ); ?>> Dry run (change nothing, just show the result)</label><br>
						<label><input type="checkbox" name="no_photos" value="1"> Do not download photos</label>
					</td>
				</tr>
			</table>
			<?php submit_button( 'Run import' ); ?>
		</form>

		<?php if ( is_array( $log ) ) : ?>
			<?php $counts = array_count_values( wp_list_pluck( $log, 'action' ) ); ?>
			<h2><?php echo $dry ? 'Dry run result (nothing changed)' : 'Import result'; ?></h2>
			<p>
				<?php
				$parts = array();
				foreach ( $counts as $k => $v ) {
					$parts[] = $v . ' ' . $k;
				}
				echo esc_html( implode( ' · ', $parts ) );
				?>
			</p>
			<table class="widefat striped">
				<thead><tr><th>Row</th><th>Action</th><th>Entry</th><th>Note</th></tr></thead>
				<tbody>
				<?php foreach ( $log as $l ) : ?>
					<tr>
						<td><?php echo (int) $l['line']; ?></td>
						<td><?php echo esc_html( $l['action'] ); ?></td>
						<td><?php echo esc_html( $l['item'] ); ?></td>
						<td><?php echo esc_html( $l['note'] ); ?></td>
					</tr>
				<?php endforeach; ?>
				</tbody>
			</table>
		<?php endif; ?>
	</div>
	<?php
}
