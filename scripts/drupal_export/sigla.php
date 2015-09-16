$view = new view();
$view->name = 'abbott_export_sigla';
$view->description = '';
$view->tag = 'default';
$view->base_table = 'node';
$view->human_name = 'Abbott: Export Sigla';
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
/* Field: Content: Siglum */
$handler->display->display_options['fields']['field_siglum']['id'] = 'field_siglum';
$handler->display->display_options['fields']['field_siglum']['table'] = 'field_data_field_siglum';
$handler->display->display_options['fields']['field_siglum']['field'] = 'field_siglum';
$handler->display->display_options['fields']['field_siglum']['label'] = 'name';
$handler->display->display_options['fields']['field_siglum']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_siglum']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_siglum']['type'] = 'text_plain';
/* Field: Content: Title */
$handler->display->display_options['fields']['title']['id'] = 'title';
$handler->display->display_options['fields']['title']['table'] = 'node';
$handler->display->display_options['fields']['title']['field'] = 'title';
$handler->display->display_options['fields']['title']['label'] = 'description';
$handler->display->display_options['fields']['title']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['title']['alter']['word_boundary'] = FALSE;
$handler->display->display_options['fields']['title']['alter']['ellipsis'] = FALSE;
$handler->display->display_options['fields']['title']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['title']['link_to_node'] = FALSE;
/* Field: Content: Nid */
$handler->display->display_options['fields']['nid']['id'] = 'nid';
$handler->display->display_options['fields']['nid']['table'] = 'node';
$handler->display->display_options['fields']['nid']['field'] = 'nid';
$handler->display->display_options['fields']['nid']['label'] = 'id';
$handler->display->display_options['fields']['nid']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['nid']['alter']['strip_tags'] = TRUE;
/* Sort criterion: Content: Siglum (field_siglum) */
$handler->display->display_options['sorts']['field_siglum_value']['id'] = 'field_siglum_value';
$handler->display->display_options['sorts']['field_siglum_value']['table'] = 'field_data_field_siglum';
$handler->display->display_options['sorts']['field_siglum_value']['field'] = 'field_siglum_value';
/* Sort criterion: Content: Title */
$handler->display->display_options['sorts']['title']['id'] = 'title';
$handler->display->display_options['sorts']['title']['table'] = 'node';
$handler->display->display_options['sorts']['title']['field'] = 'title';
/* Filter criterion: Content: Type */
$handler->display->display_options['filters']['type']['id'] = 'type';
$handler->display->display_options['filters']['type']['table'] = 'node';
$handler->display->display_options['filters']['type']['field'] = 'type';
$handler->display->display_options['filters']['type']['value'] = array(
  'source' => 'source',
);
/* Filter criterion: Content: Published or admin */
$handler->display->display_options['filters']['status_extra']['id'] = 'status_extra';
$handler->display->display_options['filters']['status_extra']['table'] = 'node';
$handler->display->display_options['filters']['status_extra']['field'] = 'status_extra';

/* Display: Data export */
$handler = $view->new_display('views_data_export', 'Data export', 'views_data_export_1');
$handler->display->display_options['pager']['type'] = 'none';
$handler->display->display_options['pager']['options']['offset'] = '0';
$handler->display->display_options['style_plugin'] = 'views_data_export_xml';
$handler->display->display_options['style_options']['provide_file'] = 1;
$handler->display->display_options['style_options']['filename'] = 'list_of_sigla.xml';
$handler->display->display_options['style_options']['parent_sort'] = 0;
$handler->display->display_options['style_options']['transform'] = 1;
$handler->display->display_options['style_options']['transform_type'] = 'underline';
$handler->display->display_options['style_options']['root_node'] = 'sigla';
$handler->display->display_options['style_options']['item_node'] = 'siglum';
$handler->display->display_options['style_options']['no_entity_encode'] = array(
  'field_siglum' => 'field_siglum',
  'title' => 'title',
  'nid' => 'nid',
);
$handler->display->display_options['path'] = 'export-sigla';
