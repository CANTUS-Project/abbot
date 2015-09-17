$view = new view();
$view->name = 'abbot_export_sources';
$view->description = '';
$view->tag = 'default';
$view->base_table = 'node';
$view->human_name = 'Abbot: Export Sources';
$view->core = 7;
$view->api_version = '3.0';
$view->disabled = FALSE; /* Edit this to true to make a default view disabled initially */

/* Display: Master */
$handler = $view->new_display('default', 'Master', 'default');
$handler->display->display_options['use_more_always'] = FALSE;
$handler->display->display_options['access']['type'] = 'perm';
$handler->display->display_options['cache']['type'] = 'none';
$handler->display->display_options['query']['type'] = 'views_query';
$handler->display->display_options['exposed_form']['type'] = 'basic';
$handler->display->display_options['pager']['type'] = 'full';
$handler->display->display_options['style_plugin'] = 'default';
$handler->display->display_options['row_plugin'] = 'fields';
/* Field: Content: Nid */
$handler->display->display_options['fields']['nid']['id'] = 'nid';
$handler->display->display_options['fields']['nid']['table'] = 'node';
$handler->display->display_options['fields']['nid']['field'] = 'nid';
$handler->display->display_options['fields']['nid']['label'] = 'id';
$handler->display->display_options['fields']['nid']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['nid']['alter']['strip_tags'] = TRUE;
/* Field: Content: Title */
$handler->display->display_options['fields']['title']['id'] = 'title';
$handler->display->display_options['fields']['title']['table'] = 'node';
$handler->display->display_options['fields']['title']['field'] = 'title';
$handler->display->display_options['fields']['title']['label'] = 'title';
$handler->display->display_options['fields']['title']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['title']['alter']['word_boundary'] = FALSE;
$handler->display->display_options['fields']['title']['alter']['ellipsis'] = FALSE;
$handler->display->display_options['fields']['title']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['title']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['title']['link_to_node'] = FALSE;
/* Field: Content: RISM */
$handler->display->display_options['fields']['field_rism']['id'] = 'field_rism';
$handler->display->display_options['fields']['field_rism']['table'] = 'field_data_field_rism';
$handler->display->display_options['fields']['field_rism']['field'] = 'field_rism';
$handler->display->display_options['fields']['field_rism']['label'] = 'rism';
$handler->display->display_options['fields']['field_rism']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_rism']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_rism']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_rism']['type'] = 'taxonomy_term_reference_plain';
/* Field: Content: Siglum */
$handler->display->display_options['fields']['field_siglum_chant']['id'] = 'field_siglum_chant';
$handler->display->display_options['fields']['field_siglum_chant']['table'] = 'field_data_field_siglum_chant';
$handler->display->display_options['fields']['field_siglum_chant']['field'] = 'field_siglum_chant';
$handler->display->display_options['fields']['field_siglum_chant']['label'] = 'siglum';
$handler->display->display_options['fields']['field_siglum_chant']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_siglum_chant']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_siglum_chant']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_siglum_chant']['type'] = 'text_plain';
/* Field: Content: Provenance */
$handler->display->display_options['fields']['field_provenance_tax']['id'] = 'field_provenance_tax';
$handler->display->display_options['fields']['field_provenance_tax']['table'] = 'field_data_field_provenance_tax';
$handler->display->display_options['fields']['field_provenance_tax']['field'] = 'field_provenance_tax';
$handler->display->display_options['fields']['field_provenance_tax']['label'] = 'provenance_id';
$handler->display->display_options['fields']['field_provenance_tax']['alter']['alter_text'] = TRUE;
$handler->display->display_options['fields']['field_provenance_tax']['alter']['text'] = '[field_provenance_tax-tid]';
$handler->display->display_options['fields']['field_provenance_tax']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_provenance_tax']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_provenance_tax']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_provenance_tax']['type'] = 'taxonomy_term_reference_plain';
/* Field: Content: Provenance notes */
$handler->display->display_options['fields']['field_provenance']['id'] = 'field_provenance';
$handler->display->display_options['fields']['field_provenance']['table'] = 'field_data_field_provenance';
$handler->display->display_options['fields']['field_provenance']['field'] = 'field_provenance';
$handler->display->display_options['fields']['field_provenance']['label'] = 'provenance_detail';
$handler->display->display_options['fields']['field_provenance']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_provenance']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_provenance']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_provenance']['type'] = 'text_plain';
/* Field: Content: Date */
$handler->display->display_options['fields']['field_date']['id'] = 'field_date';
$handler->display->display_options['fields']['field_date']['table'] = 'field_data_field_date';
$handler->display->display_options['fields']['field_date']['field'] = 'field_date';
$handler->display->display_options['fields']['field_date']['label'] = 'date';
$handler->display->display_options['fields']['field_date']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_date']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_date']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_date']['type'] = 'text_plain';
/* Field: Content: Century */
$handler->display->display_options['fields']['field_century']['id'] = 'field_century';
$handler->display->display_options['fields']['field_century']['table'] = 'field_data_field_century';
$handler->display->display_options['fields']['field_century']['field'] = 'field_century';
$handler->display->display_options['fields']['field_century']['label'] = 'century_id';
$handler->display->display_options['fields']['field_century']['alter']['alter_text'] = TRUE;
$handler->display->display_options['fields']['field_century']['alter']['text'] = '[field_century-tid]';
$handler->display->display_options['fields']['field_century']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_century']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_century']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_century']['type'] = 'taxonomy_term_reference_plain';
$handler->display->display_options['fields']['field_century']['group_rows'] = FALSE;
$handler->display->display_options['fields']['field_century']['delta_offset'] = '0';
/* Field: Content: Notation */
$handler->display->display_options['fields']['field_notation']['id'] = 'field_notation';
$handler->display->display_options['fields']['field_notation']['table'] = 'field_data_field_notation';
$handler->display->display_options['fields']['field_notation']['field'] = 'field_notation';
$handler->display->display_options['fields']['field_notation']['label'] = 'notation_style_id';
$handler->display->display_options['fields']['field_notation']['alter']['alter_text'] = TRUE;
$handler->display->display_options['fields']['field_notation']['alter']['text'] = '[field_notation-tid]';
$handler->display->display_options['fields']['field_notation']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_notation']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_notation']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_notation']['type'] = 'taxonomy_term_reference_plain';
$handler->display->display_options['fields']['field_notation']['group_rows'] = FALSE;
$handler->display->display_options['fields']['field_notation']['delta_offset'] = '0';
/* Field: Content: Editors */
$handler->display->display_options['fields']['field_editors']['id'] = 'field_editors';
$handler->display->display_options['fields']['field_editors']['table'] = 'field_data_field_editors';
$handler->display->display_options['fields']['field_editors']['field'] = 'field_editors';
$handler->display->display_options['fields']['field_editors']['label'] = 'editors';
$handler->display->display_options['fields']['field_editors']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_editors']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_editors']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_editors']['type'] = 'user_reference_uid';
$handler->display->display_options['fields']['field_editors']['group_rows'] = FALSE;
$handler->display->display_options['fields']['field_editors']['delta_offset'] = '0';
/* Field: Content: Author uid */
$handler->display->display_options['fields']['uid']['id'] = 'uid';
$handler->display->display_options['fields']['uid']['table'] = 'node';
$handler->display->display_options['fields']['uid']['field'] = 'uid';
$handler->display->display_options['fields']['uid']['label'] = 'indexers';
$handler->display->display_options['fields']['uid']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['uid']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['uid']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['uid']['link_to_user'] = FALSE;
/* Field: Content: Proofreader */
$handler->display->display_options['fields']['field_proofreader']['id'] = 'field_proofreader';
$handler->display->display_options['fields']['field_proofreader']['table'] = 'field_data_field_proofreader';
$handler->display->display_options['fields']['field_proofreader']['field'] = 'field_proofreader';
$handler->display->display_options['fields']['field_proofreader']['label'] = 'proofreaders';
$handler->display->display_options['fields']['field_proofreader']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_proofreader']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_proofreader']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_proofreader']['type'] = 'node_reference_nid';
$handler->display->display_options['fields']['field_proofreader']['group_rows'] = FALSE;
$handler->display->display_options['fields']['field_proofreader']['delta_offset'] = '0';
/* Field: Content: Segment */
$handler->display->display_options['fields']['field_segment']['id'] = 'field_segment';
$handler->display->display_options['fields']['field_segment']['table'] = 'field_data_field_segment';
$handler->display->display_options['fields']['field_segment']['field'] = 'field_segment';
$handler->display->display_options['fields']['field_segment']['label'] = 'segment_id';
$handler->display->display_options['fields']['field_segment']['alter']['alter_text'] = TRUE;
$handler->display->display_options['fields']['field_segment']['alter']['text'] = '[field_segment-tid]';
$handler->display->display_options['fields']['field_segment']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_segment']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_segment']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_segment']['type'] = 'taxonomy_term_reference_plain';
/* Field: Content: Source status */
$handler->display->display_options['fields']['field_source_status_tax']['id'] = 'field_source_status_tax';
$handler->display->display_options['fields']['field_source_status_tax']['table'] = 'field_data_field_source_status_tax';
$handler->display->display_options['fields']['field_source_status_tax']['field'] = 'field_source_status_tax';
$handler->display->display_options['fields']['field_source_status_tax']['label'] = 'source_status_id';
$handler->display->display_options['fields']['field_source_status_tax']['alter']['alter_text'] = TRUE;
$handler->display->display_options['fields']['field_source_status_tax']['alter']['text'] = '[field_source_status_tax-tid]';
$handler->display->display_options['fields']['field_source_status_tax']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_source_status_tax']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_source_status_tax']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_source_status_tax']['type'] = 'taxonomy_term_reference_plain';
/* Field: Content: Summary */
$handler->display->display_options['fields']['field_summary']['id'] = 'field_summary';
$handler->display->display_options['fields']['field_summary']['table'] = 'field_data_field_summary';
$handler->display->display_options['fields']['field_summary']['field'] = 'field_summary';
$handler->display->display_options['fields']['field_summary']['label'] = 'summary';
$handler->display->display_options['fields']['field_summary']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_summary']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_summary']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_summary']['type'] = 'text_plain';
/* Field: Content: Liturgical occasions */
$handler->display->display_options['fields']['field_liturgical_occasions']['id'] = 'field_liturgical_occasions';
$handler->display->display_options['fields']['field_liturgical_occasions']['table'] = 'field_data_field_liturgical_occasions';
$handler->display->display_options['fields']['field_liturgical_occasions']['field'] = 'field_liturgical_occasions';
$handler->display->display_options['fields']['field_liturgical_occasions']['label'] = 'liturgical_occasions';
$handler->display->display_options['fields']['field_liturgical_occasions']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_liturgical_occasions']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_liturgical_occasions']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_liturgical_occasions']['type'] = 'text_plain';
/* Field: Content: Body */
$handler->display->display_options['fields']['body']['id'] = 'body';
$handler->display->display_options['fields']['body']['table'] = 'field_data_body';
$handler->display->display_options['fields']['body']['field'] = 'body';
$handler->display->display_options['fields']['body']['label'] = 'description';
$handler->display->display_options['fields']['body']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['body']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['body']['alter']['preserve_tags'] = '<a> <p> <br>';
$handler->display->display_options['fields']['body']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['body']['type'] = 'text_plain';
/* Field: Content: Indexing notes */
$handler->display->display_options['fields']['field_indexing_notes']['id'] = 'field_indexing_notes';
$handler->display->display_options['fields']['field_indexing_notes']['table'] = 'field_data_field_indexing_notes';
$handler->display->display_options['fields']['field_indexing_notes']['field'] = 'field_indexing_notes';
$handler->display->display_options['fields']['field_indexing_notes']['label'] = 'indexing_notes';
$handler->display->display_options['fields']['field_indexing_notes']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_indexing_notes']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_indexing_notes']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_indexing_notes']['type'] = 'text_plain';
$handler->display->display_options['fields']['field_indexing_notes']['settings'] = array(
  'trim_length' => '600',
);
/* Field: Content: Indexing date */
$handler->display->display_options['fields']['field_indexing_date']['id'] = 'field_indexing_date';
$handler->display->display_options['fields']['field_indexing_date']['table'] = 'field_data_field_indexing_date';
$handler->display->display_options['fields']['field_indexing_date']['field'] = 'field_indexing_date';
$handler->display->display_options['fields']['field_indexing_date']['label'] = 'indexing_date';
$handler->display->display_options['fields']['field_indexing_date']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_indexing_date']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_indexing_date']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_indexing_date']['type'] = 'text_plain';
/* Field: Content: Image link */
$handler->display->display_options['fields']['field_image_link']['id'] = 'field_image_link';
$handler->display->display_options['fields']['field_image_link']['table'] = 'field_data_field_image_link';
$handler->display->display_options['fields']['field_image_link']['field'] = 'field_image_link';
$handler->display->display_options['fields']['field_image_link']['label'] = 'image_link';
$handler->display->display_options['fields']['field_image_link']['alter']['text'] = '[field_image_link]';
$handler->display->display_options['fields']['field_image_link']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_image_link']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_image_link']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_image_link']['type'] = 'text_plain';
/* Field: Content: Path */
$handler->display->display_options['fields']['path']['id'] = 'path';
$handler->display->display_options['fields']['path']['table'] = 'node';
$handler->display->display_options['fields']['path']['field'] = 'path';
$handler->display->display_options['fields']['path']['label'] = 'drupal_path';
$handler->display->display_options['fields']['path']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['path']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['path']['hide_empty'] = TRUE;
/* Sort criterion: Content: Siglum (field_siglum) */
$handler->display->display_options['sorts']['field_siglum_value']['id'] = 'field_siglum_value';
$handler->display->display_options['sorts']['field_siglum_value']['table'] = 'field_data_field_siglum';
$handler->display->display_options['sorts']['field_siglum_value']['field'] = 'field_siglum_value';
/* Filter criterion: Content: Published */
$handler->display->display_options['filters']['status']['id'] = 'status';
$handler->display->display_options['filters']['status']['table'] = 'node';
$handler->display->display_options['filters']['status']['field'] = 'status';
$handler->display->display_options['filters']['status']['value'] = 1;
$handler->display->display_options['filters']['status']['group'] = 1;
$handler->display->display_options['filters']['status']['expose']['operator'] = FALSE;
/* Filter criterion: Content: Type */
$handler->display->display_options['filters']['type']['id'] = 'type';
$handler->display->display_options['filters']['type']['table'] = 'node';
$handler->display->display_options['filters']['type']['field'] = 'type';
$handler->display->display_options['filters']['type']['value'] = array(
  'source' => 'source',
);

/* Display: Data export */
$handler = $view->new_display('views_data_export', 'Data export', 'views_data_export_1');
$handler->display->display_options['pager']['type'] = 'none';
$handler->display->display_options['pager']['options']['offset'] = '0';
$handler->display->display_options['style_plugin'] = 'views_data_export_xml';
$handler->display->display_options['style_options']['provide_file'] = 1;
$handler->display->display_options['style_options']['filename'] = 'list_of_sources.xml';
$handler->display->display_options['style_options']['parent_sort'] = 0;
$handler->display->display_options['style_options']['transform'] = 1;
$handler->display->display_options['style_options']['transform_type'] = 'underline';
$handler->display->display_options['style_options']['root_node'] = 'sources';
$handler->display->display_options['style_options']['item_node'] = 'source';
$handler->display->display_options['style_options']['no_entity_encode'] = array(
  'title' => 'title',
);
$handler->display->display_options['path'] = 'export-sources';
