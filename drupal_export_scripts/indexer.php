$view = new view();
$view->name = 'abbot_export_indexers';
$view->description = '';
$view->tag = 'default';
$view->base_table = 'node';
$view->human_name = 'Abbot: Export Indexers';
$view->core = 7;
$view->api_version = '3.0';
$view->disabled = FALSE; /* Edit this to true to make a default view disabled initially */

/* Display: Master */
$handler = $view->new_display('default', 'Master', 'default');
$handler->display->display_options['title'] = 'List of indexers';
$handler->display->display_options['use_ajax'] = TRUE;
$handler->display->display_options['use_more_always'] = FALSE;
$handler->display->display_options['group_by'] = TRUE;
$handler->display->display_options['access']['type'] = 'perm';
$handler->display->display_options['cache']['type'] = 'none';
$handler->display->display_options['query']['type'] = 'views_query';
$handler->display->display_options['exposed_form']['type'] = 'basic';
$handler->display->display_options['exposed_form']['options']['autosubmit'] = TRUE;
$handler->display->display_options['pager']['type'] = 'full';
$handler->display->display_options['pager']['options']['items_per_page'] = '100';
$handler->display->display_options['style_plugin'] = 'grid';
$handler->display->display_options['style_options']['columns'] = '3';
$handler->display->display_options['row_plugin'] = 'fields';
$handler->display->display_options['row_options']['separator'] = ' | ';
/* Header: Global: Result summary */
$handler->display->display_options['header']['result']['id'] = 'result';
$handler->display->display_options['header']['result']['table'] = 'views';
$handler->display->display_options['header']['result']['field'] = 'result';
$handler->display->display_options['header']['result']['content'] = 'Displaying @start - @end of <b>@total</b>';
/* Relationship: Content: Indexer (field_indexer) - reverse */
$handler->display->display_options['relationships']['reverse_field_indexer_node']['id'] = 'reverse_field_indexer_node';
$handler->display->display_options['relationships']['reverse_field_indexer_node']['table'] = 'node';
$handler->display->display_options['relationships']['reverse_field_indexer_node']['field'] = 'reverse_field_indexer_node';
/* Field: Content: Title */
$handler->display->display_options['fields']['title']['id'] = 'title';
$handler->display->display_options['fields']['title']['table'] = 'node';
$handler->display->display_options['fields']['title']['field'] = 'title';
$handler->display->display_options['fields']['title']['label'] = 'display_name';
$handler->display->display_options['fields']['title']['alter']['word_boundary'] = FALSE;
$handler->display->display_options['fields']['title']['alter']['ellipsis'] = FALSE;
$handler->display->display_options['fields']['title']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['title']['element_default_classes'] = FALSE;
$handler->display->display_options['fields']['title']['link_to_node'] = FALSE;
/* Field: Content: Institution */
$handler->display->display_options['fields']['field_indexer_institution']['id'] = 'field_indexer_institution';
$handler->display->display_options['fields']['field_indexer_institution']['table'] = 'field_data_field_indexer_institution';
$handler->display->display_options['fields']['field_indexer_institution']['field'] = 'field_indexer_institution';
$handler->display->display_options['fields']['field_indexer_institution']['label'] = 'institution';
$handler->display->display_options['fields']['field_indexer_institution']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_indexer_institution']['element_default_classes'] = FALSE;
$handler->display->display_options['fields']['field_indexer_institution']['type'] = 'text_plain';
/* Field: Content: City */
$handler->display->display_options['fields']['field_indexer_city']['id'] = 'field_indexer_city';
$handler->display->display_options['fields']['field_indexer_city']['table'] = 'field_data_field_indexer_city';
$handler->display->display_options['fields']['field_indexer_city']['field'] = 'field_indexer_city';
$handler->display->display_options['fields']['field_indexer_city']['label'] = 'city';
$handler->display->display_options['fields']['field_indexer_city']['alter']['text'] = '[field_indexer_city] - ';
$handler->display->display_options['fields']['field_indexer_city']['type'] = 'text_plain';
/* Field: Content: Country */
$handler->display->display_options['fields']['field_indexer_country']['id'] = 'field_indexer_country';
$handler->display->display_options['fields']['field_indexer_country']['table'] = 'field_data_field_indexer_country';
$handler->display->display_options['fields']['field_indexer_country']['field'] = 'field_indexer_country';
$handler->display->display_options['fields']['field_indexer_country']['label'] = 'country';
$handler->display->display_options['fields']['field_indexer_country']['element_type'] = 'strong';
$handler->display->display_options['fields']['field_indexer_country']['type'] = 'text_plain';
/* Field: Content: Nid */
$handler->display->display_options['fields']['nid_1']['id'] = 'nid_1';
$handler->display->display_options['fields']['nid_1']['table'] = 'node';
$handler->display->display_options['fields']['nid_1']['field'] = 'nid';
$handler->display->display_options['fields']['nid_1']['label'] = 'id';
/* Field: Content: Family name */
$handler->display->display_options['fields']['field_family_name']['id'] = 'field_family_name';
$handler->display->display_options['fields']['field_family_name']['table'] = 'field_data_field_family_name';
$handler->display->display_options['fields']['field_family_name']['field'] = 'field_family_name';
$handler->display->display_options['fields']['field_family_name']['label'] = 'family_name';
$handler->display->display_options['fields']['field_family_name']['type'] = 'text_plain';
/* Field: Content: First name */
$handler->display->display_options['fields']['field_first_name']['id'] = 'field_first_name';
$handler->display->display_options['fields']['field_first_name']['table'] = 'field_data_field_first_name';
$handler->display->display_options['fields']['field_first_name']['field'] = 'field_first_name';
$handler->display->display_options['fields']['field_first_name']['label'] = 'given_name';
$handler->display->display_options['fields']['field_first_name']['type'] = 'text_plain';
/* Field: Content: Path */
$handler->display->display_options['fields']['path']['id'] = 'path';
$handler->display->display_options['fields']['path']['table'] = 'node';
$handler->display->display_options['fields']['path']['field'] = 'path';
$handler->display->display_options['fields']['path']['label'] = 'drupal_path';
$handler->display->display_options['fields']['path']['alter']['strip_tags'] = TRUE;
/* Sort criterion: Content: Family name (field_family_name) */
$handler->display->display_options['sorts']['field_family_name_value']['id'] = 'field_family_name_value';
$handler->display->display_options['sorts']['field_family_name_value']['table'] = 'field_data_field_family_name';
$handler->display->display_options['sorts']['field_family_name_value']['field'] = 'field_family_name_value';
/* Sort criterion: Content: First name (field_first_name) */
$handler->display->display_options['sorts']['field_first_name_value']['id'] = 'field_first_name_value';
$handler->display->display_options['sorts']['field_first_name_value']['table'] = 'field_data_field_first_name';
$handler->display->display_options['sorts']['field_first_name_value']['field'] = 'field_first_name_value';
/* Filter criterion: Content: Type */
$handler->display->display_options['filters']['type']['id'] = 'type';
$handler->display->display_options['filters']['type']['table'] = 'node';
$handler->display->display_options['filters']['type']['field'] = 'type';
$handler->display->display_options['filters']['type']['value'] = array(
  'indexer' => 'indexer',
);
/* Filter criterion: Global: Combine fields filter */
$handler->display->display_options['filters']['combine']['id'] = 'combine';
$handler->display->display_options['filters']['combine']['table'] = 'views';
$handler->display->display_options['filters']['combine']['field'] = 'combine';
$handler->display->display_options['filters']['combine']['operator'] = 'contains';
$handler->display->display_options['filters']['combine']['exposed'] = TRUE;
$handler->display->display_options['filters']['combine']['expose']['operator_id'] = 'combine_op';
$handler->display->display_options['filters']['combine']['expose']['label'] = 'Search indexers';
$handler->display->display_options['filters']['combine']['expose']['description'] = 'Type any part of a word';
$handler->display->display_options['filters']['combine']['expose']['operator'] = 'combine_op';
$handler->display->display_options['filters']['combine']['expose']['identifier'] = 'combine';
$handler->display->display_options['filters']['combine']['expose']['remember_roles'] = array(
  2 => '2',
  1 => 0,
  3 => 0,
  5 => 0,
  4 => 0,
  6 => 0,
);
$handler->display->display_options['filters']['combine']['fields'] = array(
  'title' => 'title',
  'field_indexer_institution' => 'field_indexer_institution',
  'field_indexer_city' => 'field_indexer_city',
  'field_indexer_country' => 'field_indexer_country',
);

/* Display: Data export */
$handler = $view->new_display('views_data_export', 'Data export', 'views_data_export_1');
$handler->display->display_options['pager']['type'] = 'none';
$handler->display->display_options['pager']['options']['offset'] = '0';
$handler->display->display_options['style_plugin'] = 'views_data_export_xml';
$handler->display->display_options['style_options']['provide_file'] = 1;
$handler->display->display_options['style_options']['filename'] = 'list_of_indexers.xml';
$handler->display->display_options['style_options']['parent_sort'] = 0;
$handler->display->display_options['style_options']['transform'] = 1;
$handler->display->display_options['style_options']['transform_type'] = 'underline';
$handler->display->display_options['style_options']['root_node'] = 'indexers';
$handler->display->display_options['style_options']['item_node'] = 'indexer';
$handler->display->display_options['style_options']['no_entity_encode'] = array(
  'title' => 'title',
  'field_indexer_institution' => 'field_indexer_institution',
  'field_indexer_city' => 'field_indexer_city',
  'field_indexer_country' => 'field_indexer_country',
  'nid_1' => 'nid_1',
);
$handler->display->display_options['path'] = 'export-indexers';
