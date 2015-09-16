$view = new view();
$view->name = 'abbott_export_chants';
$view->description = '';
$view->tag = 'default';
$view->base_table = 'node';
$view->human_name = 'Abbott: Export Chants';
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
$handler->display->display_options['pager']['type'] = 'some';
$handler->display->display_options['pager']['options']['items_per_page'] = '10';
$handler->display->display_options['pager']['options']['offset'] = '0';
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
$handler->display->display_options['fields']['title']['label'] = 'incipit';
$handler->display->display_options['fields']['title']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['title']['alter']['word_boundary'] = FALSE;
$handler->display->display_options['fields']['title']['alter']['ellipsis'] = FALSE;
$handler->display->display_options['fields']['title']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['title']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['title']['link_to_node'] = FALSE;
/* Field: Content: Nid */
$handler->display->display_options['fields']['nid_1']['id'] = 'nid_1';
$handler->display->display_options['fields']['nid_1']['table'] = 'node';
$handler->display->display_options['fields']['nid_1']['field'] = 'nid';
$handler->display->display_options['fields']['nid_1']['label'] = 'drupal_path';
$handler->display->display_options['fields']['nid_1']['alter']['alter_text'] = TRUE;
$handler->display->display_options['fields']['nid_1']['alter']['text'] = '/chant/[nid]/';
$handler->display->display_options['fields']['nid_1']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['nid_1']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['nid_1']['hide_empty'] = TRUE;
/* Field: Content: Source */
$handler->display->display_options['fields']['field_source']['id'] = 'field_source';
$handler->display->display_options['fields']['field_source']['table'] = 'field_data_field_source';
$handler->display->display_options['fields']['field_source']['field'] = 'field_source';
$handler->display->display_options['fields']['field_source']['label'] = 'source_id';
$handler->display->display_options['fields']['field_source']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_source']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_source']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_source']['type'] = 'entityreference_entity_id';
$handler->display->display_options['fields']['field_source']['settings'] = array(
  'link' => 0,
);
/* Field: Content: Marginalia */
$handler->display->display_options['fields']['field_marginalia']['id'] = 'field_marginalia';
$handler->display->display_options['fields']['field_marginalia']['table'] = 'field_data_field_marginalia';
$handler->display->display_options['fields']['field_marginalia']['field'] = 'field_marginalia';
$handler->display->display_options['fields']['field_marginalia']['label'] = 'marginalia';
$handler->display->display_options['fields']['field_marginalia']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_marginalia']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_marginalia']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_marginalia']['type'] = 'text_plain';
/* Field: Content: Folio */
$handler->display->display_options['fields']['field_folio']['id'] = 'field_folio';
$handler->display->display_options['fields']['field_folio']['table'] = 'field_data_field_folio';
$handler->display->display_options['fields']['field_folio']['field'] = 'field_folio';
$handler->display->display_options['fields']['field_folio']['label'] = 'folio';
$handler->display->display_options['fields']['field_folio']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_folio']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_folio']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_folio']['type'] = 'text_plain';
/* Field: Content: Sequence */
$handler->display->display_options['fields']['field_sequence']['id'] = 'field_sequence';
$handler->display->display_options['fields']['field_sequence']['table'] = 'field_data_field_sequence';
$handler->display->display_options['fields']['field_sequence']['field'] = 'field_sequence';
$handler->display->display_options['fields']['field_sequence']['label'] = 'sequence';
$handler->display->display_options['fields']['field_sequence']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_sequence']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_sequence']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_sequence']['settings'] = array(
  'thousand_separator' => ' ',
  'prefix_suffix' => 1,
);
/* Field: Content: Office */
$handler->display->display_options['fields']['field_office']['id'] = 'field_office';
$handler->display->display_options['fields']['field_office']['table'] = 'field_data_field_office';
$handler->display->display_options['fields']['field_office']['field'] = 'field_office';
$handler->display->display_options['fields']['field_office']['label'] = 'office_id';
$handler->display->display_options['fields']['field_office']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_office']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_office']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_office']['type'] = 'entityreference_entity_id';
$handler->display->display_options['fields']['field_office']['settings'] = array(
  'link' => 0,
);
/* Field: Content: Genre */
$handler->display->display_options['fields']['field_mc_genre']['id'] = 'field_mc_genre';
$handler->display->display_options['fields']['field_mc_genre']['table'] = 'field_data_field_mc_genre';
$handler->display->display_options['fields']['field_mc_genre']['field'] = 'field_mc_genre';
$handler->display->display_options['fields']['field_mc_genre']['label'] = 'genre_id';
$handler->display->display_options['fields']['field_mc_genre']['alter']['alter_text'] = TRUE;
$handler->display->display_options['fields']['field_mc_genre']['alter']['text'] = '[field_mc_genre-tid]';
$handler->display->display_options['fields']['field_mc_genre']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_mc_genre']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_mc_genre']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_mc_genre']['type'] = 'taxonomy_term_reference_plain';
/* Field: Content: Position */
$handler->display->display_options['fields']['field_position']['id'] = 'field_position';
$handler->display->display_options['fields']['field_position']['table'] = 'field_data_field_position';
$handler->display->display_options['fields']['field_position']['field'] = 'field_position';
$handler->display->display_options['fields']['field_position']['label'] = 'position';
$handler->display->display_options['fields']['field_position']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_position']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_position']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_position']['type'] = 'text_plain';
/* Field: Content: Cantus ID */
$handler->display->display_options['fields']['field_cantus_id']['id'] = 'field_cantus_id';
$handler->display->display_options['fields']['field_cantus_id']['table'] = 'field_data_field_cantus_id';
$handler->display->display_options['fields']['field_cantus_id']['field'] = 'field_cantus_id';
$handler->display->display_options['fields']['field_cantus_id']['label'] = 'cantus_id';
$handler->display->display_options['fields']['field_cantus_id']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_cantus_id']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_cantus_id']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_cantus_id']['type'] = 'text_plain';
/* Field: Content: Feast */
$handler->display->display_options['fields']['field_mc_feast']['id'] = 'field_mc_feast';
$handler->display->display_options['fields']['field_mc_feast']['table'] = 'field_data_field_mc_feast';
$handler->display->display_options['fields']['field_mc_feast']['field'] = 'field_mc_feast';
$handler->display->display_options['fields']['field_mc_feast']['label'] = 'feast_id';
$handler->display->display_options['fields']['field_mc_feast']['alter']['alter_text'] = TRUE;
$handler->display->display_options['fields']['field_mc_feast']['alter']['text'] = '[field_mc_feast-tid]';
$handler->display->display_options['fields']['field_mc_feast']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_mc_feast']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_mc_feast']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_mc_feast']['type'] = 'taxonomy_term_reference_plain';
/* Field: Content: Mode */
$handler->display->display_options['fields']['field_mode']['id'] = 'field_mode';
$handler->display->display_options['fields']['field_mode']['table'] = 'field_data_field_mode';
$handler->display->display_options['fields']['field_mode']['field'] = 'field_mode';
$handler->display->display_options['fields']['field_mode']['label'] = 'mode';
$handler->display->display_options['fields']['field_mode']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_mode']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_mode']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_mode']['type'] = 'text_plain';
/* Field: Content: Differentia */
$handler->display->display_options['fields']['field_differentia']['id'] = 'field_differentia';
$handler->display->display_options['fields']['field_differentia']['table'] = 'field_data_field_differentia';
$handler->display->display_options['fields']['field_differentia']['field'] = 'field_differentia';
$handler->display->display_options['fields']['field_differentia']['label'] = 'differentia';
$handler->display->display_options['fields']['field_differentia']['alter']['text'] = '[field_differentia-format]';
$handler->display->display_options['fields']['field_differentia']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_differentia']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_differentia']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_differentia']['type'] = 'text_plain';
/* Field: Content: Finalis */
$handler->display->display_options['fields']['field_finalis']['id'] = 'field_finalis';
$handler->display->display_options['fields']['field_finalis']['table'] = 'field_data_field_finalis';
$handler->display->display_options['fields']['field_finalis']['field'] = 'field_finalis';
$handler->display->display_options['fields']['field_finalis']['label'] = 'finalis';
$handler->display->display_options['fields']['field_finalis']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_finalis']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_finalis']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_finalis']['type'] = 'text_plain';
/* Field: Content: Body */
$handler->display->display_options['fields']['body']['id'] = 'body';
$handler->display->display_options['fields']['body']['table'] = 'field_data_body';
$handler->display->display_options['fields']['body']['field'] = 'body';
$handler->display->display_options['fields']['body']['label'] = 'full_text';
$handler->display->display_options['fields']['body']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['body']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['body']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['body']['type'] = 'text_plain';
/* Field: Content: Full text (MS spelling) */
$handler->display->display_options['fields']['field_full_text_ms']['id'] = 'field_full_text_ms';
$handler->display->display_options['fields']['field_full_text_ms']['table'] = 'field_data_field_full_text_ms';
$handler->display->display_options['fields']['field_full_text_ms']['field'] = 'field_full_text_ms';
$handler->display->display_options['fields']['field_full_text_ms']['label'] = 'full_text_manuscript';
$handler->display->display_options['fields']['field_full_text_ms']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_full_text_ms']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_full_text_ms']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_full_text_ms']['type'] = 'text_plain';
/* Field: Content: Volpiano */
$handler->display->display_options['fields']['field_volpiano']['id'] = 'field_volpiano';
$handler->display->display_options['fields']['field_volpiano']['table'] = 'field_data_field_volpiano';
$handler->display->display_options['fields']['field_volpiano']['field'] = 'field_volpiano';
$handler->display->display_options['fields']['field_volpiano']['label'] = 'volpiano';
$handler->display->display_options['fields']['field_volpiano']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_volpiano']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_volpiano']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_volpiano']['type'] = 'text_plain';
/* Field: Content: Indexing notes */
$handler->display->display_options['fields']['field_notes']['id'] = 'field_notes';
$handler->display->display_options['fields']['field_notes']['table'] = 'field_data_field_notes';
$handler->display->display_options['fields']['field_notes']['field'] = 'field_notes';
$handler->display->display_options['fields']['field_notes']['label'] = 'notes';
$handler->display->display_options['fields']['field_notes']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_notes']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_notes']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_notes']['type'] = 'text_plain';
/* Field: Content: CAO Concordances */
$handler->display->display_options['fields']['field_cao_concordances']['id'] = 'field_cao_concordances';
$handler->display->display_options['fields']['field_cao_concordances']['table'] = 'field_data_field_cao_concordances';
$handler->display->display_options['fields']['field_cao_concordances']['field'] = 'field_cao_concordances';
$handler->display->display_options['fields']['field_cao_concordances']['label'] = 'cao_concordances';
$handler->display->display_options['fields']['field_cao_concordances']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_cao_concordances']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_cao_concordances']['type'] = 'text_plain';
/* Field: Content: Proofread by */
$handler->display->display_options['fields']['field_proofread_by']['id'] = 'field_proofread_by';
$handler->display->display_options['fields']['field_proofread_by']['table'] = 'field_data_field_proofread_by';
$handler->display->display_options['fields']['field_proofread_by']['field'] = 'field_proofread_by';
$handler->display->display_options['fields']['field_proofread_by']['label'] = 'proofreader_id';
$handler->display->display_options['fields']['field_proofread_by']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_proofread_by']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_proofread_by']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_proofread_by']['type'] = 'user_reference_uid';
$handler->display->display_options['fields']['field_proofread_by']['group_rows'] = FALSE;
$handler->display->display_options['fields']['field_proofread_by']['delta_offset'] = '0';
/* Field: Content: Fulltext proofread */
$handler->display->display_options['fields']['field_fulltext_proofread']['id'] = 'field_fulltext_proofread';
$handler->display->display_options['fields']['field_fulltext_proofread']['table'] = 'field_data_field_fulltext_proofread';
$handler->display->display_options['fields']['field_fulltext_proofread']['field'] = 'field_fulltext_proofread';
$handler->display->display_options['fields']['field_fulltext_proofread']['label'] = 'proofread_fulltext';
$handler->display->display_options['fields']['field_fulltext_proofread']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_fulltext_proofread']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_fulltext_proofread']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_fulltext_proofread']['type'] = 'list_key';
/* Field: Content: MS Fulltext proofread */
$handler->display->display_options['fields']['field_ms_fulltext_proofread']['id'] = 'field_ms_fulltext_proofread';
$handler->display->display_options['fields']['field_ms_fulltext_proofread']['table'] = 'field_data_field_ms_fulltext_proofread';
$handler->display->display_options['fields']['field_ms_fulltext_proofread']['field'] = 'field_ms_fulltext_proofread';
$handler->display->display_options['fields']['field_ms_fulltext_proofread']['label'] = 'proofread_fulltext_manuscript';
$handler->display->display_options['fields']['field_ms_fulltext_proofread']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_ms_fulltext_proofread']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_ms_fulltext_proofread']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_ms_fulltext_proofread']['type'] = 'list_key';
/* Field: Content: Volpiano proofread */
$handler->display->display_options['fields']['field_volpiano_proofread']['id'] = 'field_volpiano_proofread';
$handler->display->display_options['fields']['field_volpiano_proofread']['table'] = 'field_data_field_volpiano_proofread';
$handler->display->display_options['fields']['field_volpiano_proofread']['field'] = 'field_volpiano_proofread';
$handler->display->display_options['fields']['field_volpiano_proofread']['label'] = 'proofread_volpiano';
$handler->display->display_options['fields']['field_volpiano_proofread']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_volpiano_proofread']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_volpiano_proofread']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_volpiano_proofread']['type'] = 'list_key';
/* Field: Content: Melody ID */
$handler->display->display_options['fields']['field_melody_id']['id'] = 'field_melody_id';
$handler->display->display_options['fields']['field_melody_id']['table'] = 'field_data_field_melody_id';
$handler->display->display_options['fields']['field_melody_id']['field'] = 'field_melody_id';
$handler->display->display_options['fields']['field_melody_id']['label'] = 'melody_id';
$handler->display->display_options['fields']['field_melody_id']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_melody_id']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_melody_id']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_melody_id']['type'] = 'text_plain';
/* Field: Content: Image link */
$handler->display->display_options['fields']['field_image_link_chant']['id'] = 'field_image_link_chant';
$handler->display->display_options['fields']['field_image_link_chant']['table'] = 'field_data_field_image_link_chant';
$handler->display->display_options['fields']['field_image_link_chant']['field'] = 'field_image_link_chant';
$handler->display->display_options['fields']['field_image_link_chant']['label'] = 'image_link';
$handler->display->display_options['fields']['field_image_link_chant']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_image_link_chant']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_image_link_chant']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_image_link_chant']['type'] = 'text_plain';
/* Field: Content: Siglum */
$handler->display->display_options['fields']['field_siglum_chant']['id'] = 'field_siglum_chant';
$handler->display->display_options['fields']['field_siglum_chant']['table'] = 'field_data_field_siglum_chant';
$handler->display->display_options['fields']['field_siglum_chant']['field'] = 'field_siglum_chant';
$handler->display->display_options['fields']['field_siglum_chant']['label'] = 'siglum';
$handler->display->display_options['fields']['field_siglum_chant']['alter']['text'] = '[field_siglum_chant-value]';
$handler->display->display_options['fields']['field_siglum_chant']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_siglum_chant']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_siglum_chant']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_siglum_chant']['type'] = 'text_plain';
/* Contextual filter: Content: Updated date */
$handler->display->display_options['arguments']['changed_fulldate']['id'] = 'changed_fulldate';
$handler->display->display_options['arguments']['changed_fulldate']['table'] = 'node';
$handler->display->display_options['arguments']['changed_fulldate']['field'] = 'changed_fulldate';
$handler->display->display_options['arguments']['changed_fulldate']['default_action'] = 'empty';
$handler->display->display_options['arguments']['changed_fulldate']['default_argument_type'] = 'fixed';
$handler->display->display_options['arguments']['changed_fulldate']['summary']['number_of_records'] = '0';
$handler->display->display_options['arguments']['changed_fulldate']['summary']['format'] = 'default_summary';
$handler->display->display_options['arguments']['changed_fulldate']['summary_options']['items_per_page'] = '25';
$handler->display->display_options['arguments']['changed_fulldate']['specify_validation'] = TRUE;
$handler->display->display_options['arguments']['changed_fulldate']['validate']['type'] = 'numeric';
$handler->display->display_options['arguments']['changed_fulldate']['validate']['fail'] = 'empty';
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
  'chant' => 'chant',
);

/* Display: Data export */
$handler = $view->new_display('views_data_export', 'Data export', 'views_data_export_1');
$handler->display->display_options['pager']['type'] = 'none';
$handler->display->display_options['pager']['options']['offset'] = '0';
$handler->display->display_options['style_plugin'] = 'views_data_export_xml';
$handler->display->display_options['style_options']['provide_file'] = 1;
$handler->display->display_options['style_options']['filename'] = 'list_of_chants-%1-value.xml';
$handler->display->display_options['style_options']['parent_sort'] = 0;
$handler->display->display_options['style_options']['transform'] = 1;
$handler->display->display_options['style_options']['transform_type'] = 'underline';
$handler->display->display_options['style_options']['root_node'] = 'chants';
$handler->display->display_options['style_options']['item_node'] = 'chant';
$handler->display->display_options['style_options']['no_entity_encode'] = array(
  'title' => 'title',
  'nid' => 'nid',
  'view_node' => 'view_node',
);
$handler->display->display_options['path'] = 'export-chants/%';
