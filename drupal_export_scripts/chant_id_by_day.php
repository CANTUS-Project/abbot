$view = new view();
$view->name = 'clone_of_abbott_export_chant_ids';
$view->description = 'Given a YYYYMMDD date in the URL, export an XML file with the chant IDs that were updated/new on that day.';
$view->tag = 'default';
$view->base_table = 'node';
$view->human_name = 'Abbott: Export Chant IDs';
$view->core = 7;
$view->api_version = '3.0';
$view->disabled = FALSE; /* Edit this to true to make a default view disabled initially */

/* Display: Master */
$handler = $view->new_display('default', 'Master', 'default');
$handler->display->display_options['use_more_always'] = FALSE;
$handler->display->display_options['access']['type'] = 'none';
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
$handler->display->display_options['fields']['nid']['element_label_colon'] = FALSE;
$handler->display->display_options['fields']['nid']['element_default_classes'] = FALSE;
/* Field: Content: Updated date */
$handler->display->display_options['fields']['changed']['id'] = 'changed';
$handler->display->display_options['fields']['changed']['table'] = 'node';
$handler->display->display_options['fields']['changed']['field'] = 'changed';
$handler->display->display_options['fields']['changed']['label'] = 'updated';
$handler->display->display_options['fields']['changed']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['changed']['element_label_colon'] = FALSE;
$handler->display->display_options['fields']['changed']['element_default_classes'] = FALSE;
$handler->display->display_options['fields']['changed']['date_format'] = 'custom';
$handler->display->display_options['fields']['changed']['custom_date_format'] = 'c';
$handler->display->display_options['fields']['changed']['second_date_format'] = 'long';
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
$handler->display->display_options['defaults']['empty'] = FALSE;
$handler->display->display_options['path'] = 'export-chant-ids/%';
