$view = new view();
$view->name = 'abbot_export_feasts';
$view->description = '';
$view->tag = '';
$view->base_table = 'taxonomy_term_data';
$view->human_name = 'Abbott: Export Feasts';
$view->core = 7;
$view->api_version = '3.0';
$view->disabled = FALSE; /* Edit this to true to make a default view disabled initially */

/* Display: Defaults */
$handler = $view->new_display('default', 'Defaults', 'default');
$handler->display->display_options['title'] = 'Abbott: Export Feasts';
$handler->display->display_options['use_ajax'] = TRUE;
$handler->display->display_options['use_more_always'] = FALSE;
$handler->display->display_options['access']['type'] = 'perm';
$handler->display->display_options['cache']['type'] = 'none';
$handler->display->display_options['query']['type'] = 'views_query';
$handler->display->display_options['exposed_form']['type'] = 'basic';
$handler->display->display_options['exposed_form']['options']['autosubmit'] = TRUE;
$handler->display->display_options['pager']['type'] = 'full';
$handler->display->display_options['pager']['options']['items_per_page'] = '200';
$handler->display->display_options['pager']['options']['offset'] = '0';
$handler->display->display_options['pager']['options']['id'] = '0';
$handler->display->display_options['pager']['options']['quantity'] = '1';
$handler->display->display_options['pager']['options']['tags']['previous'] = '‹ prev';
$handler->display->display_options['style_plugin'] = 'table';
$handler->display->display_options['style_options']['grouping'] = '';
$handler->display->display_options['style_options']['columns'] = array(
  'name' => 'name',
  'description' => 'description',
);
$handler->display->display_options['style_options']['default'] = '-1';
$handler->display->display_options['style_options']['info'] = array(
  'name' => array(
    'sortable' => 0,
    'default_sort_order' => 'asc',
    'align' => '',
    'separator' => '',
  ),
  'description' => array(
    'align' => '',
    'separator' => '',
  ),
);
/* Header: Global: Result summary */
$handler->display->display_options['header']['result']['id'] = 'result';
$handler->display->display_options['header']['result']['table'] = 'views';
$handler->display->display_options['header']['result']['field'] = 'result';
/* Field: Taxonomy term: Name */
$handler->display->display_options['fields']['name']['id'] = 'name';
$handler->display->display_options['fields']['name']['table'] = 'taxonomy_term_data';
$handler->display->display_options['fields']['name']['field'] = 'name';
$handler->display->display_options['fields']['name']['label'] = 'name';
$handler->display->display_options['fields']['name']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['name']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['name']['element_type'] = 'strong';
$handler->display->display_options['fields']['name']['element_label_colon'] = FALSE;
/* Field: Taxonomy term: Term description */
$handler->display->display_options['fields']['description']['id'] = 'description';
$handler->display->display_options['fields']['description']['table'] = 'taxonomy_term_data';
$handler->display->display_options['fields']['description']['field'] = 'description';
$handler->display->display_options['fields']['description']['label'] = 'description';
$handler->display->display_options['fields']['description']['alter']['text'] = '<strong>[name]</strong><br>
[description] ';
$handler->display->display_options['fields']['description']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['description']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['description']['hide_empty'] = TRUE;
/* Field: Global: Custom text */
$handler->display->display_options['fields']['nothing']['id'] = 'nothing';
$handler->display->display_options['fields']['nothing']['table'] = 'views';
$handler->display->display_options['fields']['nothing']['field'] = 'nothing';
$handler->display->display_options['fields']['nothing']['label'] = 'Feast name';
$handler->display->display_options['fields']['nothing']['exclude'] = TRUE;
$handler->display->display_options['fields']['nothing']['alter']['text'] = '<strong>[name]</strong><br>
[description] ';
/* Field: Taxonomy term: Feast date */
$handler->display->display_options['fields']['field_feastdate']['id'] = 'field_feastdate';
$handler->display->display_options['fields']['field_feastdate']['table'] = 'field_data_field_feastdate';
$handler->display->display_options['fields']['field_feastdate']['field'] = 'field_feastdate';
$handler->display->display_options['fields']['field_feastdate']['label'] = 'date';
$handler->display->display_options['fields']['field_feastdate']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_feastdate']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_feastdate']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_feastdate']['type'] = 'text_plain';
/* Field: Taxonomy term: Feast code */
$handler->display->display_options['fields']['field_feast_code']['id'] = 'field_feast_code';
$handler->display->display_options['fields']['field_feast_code']['table'] = 'field_data_field_feast_code';
$handler->display->display_options['fields']['field_feast_code']['field'] = 'field_feast_code';
$handler->display->display_options['fields']['field_feast_code']['label'] = 'feast_code';
$handler->display->display_options['fields']['field_feast_code']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['field_feast_code']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['field_feast_code']['hide_empty'] = TRUE;
$handler->display->display_options['fields']['field_feast_code']['type'] = 'text_plain';
/* Field: Taxonomy term: Term ID */
$handler->display->display_options['fields']['tid']['id'] = 'tid';
$handler->display->display_options['fields']['tid']['table'] = 'taxonomy_term_data';
$handler->display->display_options['fields']['tid']['field'] = 'tid';
$handler->display->display_options['fields']['tid']['label'] = 'id';
$handler->display->display_options['fields']['tid']['alter']['trim_whitespace'] = TRUE;
$handler->display->display_options['fields']['tid']['alter']['strip_tags'] = TRUE;
$handler->display->display_options['fields']['tid']['separator'] = '';
/* Filter criterion: Taxonomy term: Vocabulary */
$handler->display->display_options['filters']['vid']['id'] = 'vid';
$handler->display->display_options['filters']['vid']['table'] = 'taxonomy_term_data';
$handler->display->display_options['filters']['vid']['field'] = 'vid';
$handler->display->display_options['filters']['vid']['value'] = array(
  6 => '6',
);
$handler->display->display_options['filters']['vid']['group'] = 1;
/* Filter criterion: Global: Combine fields filter */
$handler->display->display_options['filters']['combine']['id'] = 'combine';
$handler->display->display_options['filters']['combine']['table'] = 'views';
$handler->display->display_options['filters']['combine']['field'] = 'combine';
$handler->display->display_options['filters']['combine']['operator'] = 'contains';
$handler->display->display_options['filters']['combine']['group'] = 1;
$handler->display->display_options['filters']['combine']['exposed'] = TRUE;
$handler->display->display_options['filters']['combine']['expose']['operator_id'] = 'combine_op';
$handler->display->display_options['filters']['combine']['expose']['label'] = 'Search feasts / feast codes';
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
  'name' => 'name',
  'description' => 'description',
  'field_feast_code' => 'field_feast_code',
);
/* Filter criterion: Taxonomy term: Feast date (field_feastdate) */
$handler->display->display_options['filters']['field_feastdate_value']['id'] = 'field_feastdate_value';
$handler->display->display_options['filters']['field_feastdate_value']['table'] = 'field_data_field_feastdate';
$handler->display->display_options['filters']['field_feastdate_value']['field'] = 'field_feastdate_value';
$handler->display->display_options['filters']['field_feastdate_value']['group'] = 1;
$handler->display->display_options['filters']['field_feastdate_value']['exposed'] = TRUE;
$handler->display->display_options['filters']['field_feastdate_value']['expose']['operator_id'] = 'field_feastdate_value_op';
$handler->display->display_options['filters']['field_feastdate_value']['expose']['label'] = 'Feast date (field_feastdate)';
$handler->display->display_options['filters']['field_feastdate_value']['expose']['operator'] = 'field_feastdate_value_op';
$handler->display->display_options['filters']['field_feastdate_value']['expose']['identifier'] = 'field_feastdate_value';
$handler->display->display_options['filters']['field_feastdate_value']['is_grouped'] = TRUE;
$handler->display->display_options['filters']['field_feastdate_value']['group_info']['label'] = 'Temp / Sanc';
$handler->display->display_options['filters']['field_feastdate_value']['group_info']['identifier'] = 'field_feastdate_value';
$handler->display->display_options['filters']['field_feastdate_value']['group_info']['group_items'] = array(
  1 => array(
    'title' => 'Temporale',
    'operator' => 'empty',
    'value' => ' x',
  ),
  2 => array(
    'title' => 'Sanctorale',
    'operator' => 'not empty',
    'value' => ' x',
  ),
  3 => array(
    'title' => '',
    'operator' => '=',
    'value' => '',
  ),
  4 => array(
    'title' => '',
    'operator' => '=',
    'value' => '',
  ),
);
/* Filter criterion: Taxonomy term: Month (field_feastmonth) */
$handler->display->display_options['filters']['field_feastmonth_value']['id'] = 'field_feastmonth_value';
$handler->display->display_options['filters']['field_feastmonth_value']['table'] = 'field_data_field_feastmonth';
$handler->display->display_options['filters']['field_feastmonth_value']['field'] = 'field_feastmonth_value';
$handler->display->display_options['filters']['field_feastmonth_value']['group'] = 1;
$handler->display->display_options['filters']['field_feastmonth_value']['exposed'] = TRUE;
$handler->display->display_options['filters']['field_feastmonth_value']['expose']['operator_id'] = 'field_feastmonth_value_op';
$handler->display->display_options['filters']['field_feastmonth_value']['expose']['label'] = 'Month (field_feastmonth)';
$handler->display->display_options['filters']['field_feastmonth_value']['expose']['operator'] = 'field_feastmonth_value_op';
$handler->display->display_options['filters']['field_feastmonth_value']['expose']['identifier'] = 'field_feastmonth_value';
$handler->display->display_options['filters']['field_feastmonth_value']['is_grouped'] = TRUE;
$handler->display->display_options['filters']['field_feastmonth_value']['group_info']['label'] = 'Month';
$handler->display->display_options['filters']['field_feastmonth_value']['group_info']['identifier'] = 'field_feastmonth_value';
$handler->display->display_options['filters']['field_feastmonth_value']['group_info']['group_items'] = array(
  1 => array(
    'title' => 'December',
    'operator' => '=',
    'value' => array(
      'value' => '12',
      'min' => '',
      'max' => '',
    ),
  ),
  2 => array(
    'title' => 'Jan',
    'operator' => '=',
    'value' => array(
      'value' => '1',
      'min' => '',
      'max' => '',
    ),
  ),
  3 => array(
    'title' => 'Feb',
    'operator' => '=',
    'value' => array(
      'value' => '2',
      'min' => '',
      'max' => '',
    ),
  ),
  4 => array(
    'title' => 'Mar',
    'operator' => '=',
    'value' => array(
      'value' => '3',
      'min' => '',
      'max' => '',
    ),
  ),
  5 => array(
    'title' => 'Apr',
    'operator' => '=',
    'value' => array(
      'value' => '4',
      'min' => '',
      'max' => '',
    ),
  ),
  6 => array(
    'title' => 'May',
    'operator' => '=',
    'value' => array(
      'value' => '5',
      'min' => '',
      'max' => '',
    ),
  ),
  7 => array(
    'title' => 'June',
    'operator' => '=',
    'value' => array(
      'value' => '6',
      'min' => '',
      'max' => '',
    ),
  ),
  8 => array(
    'title' => 'July',
    'operator' => '=',
    'value' => array(
      'value' => '7',
      'min' => '',
      'max' => '',
    ),
  ),
  9 => array(
    'title' => 'August',
    'operator' => '=',
    'value' => array(
      'value' => '8',
      'min' => '',
      'max' => '',
    ),
  ),
  10 => array(
    'title' => 'September',
    'operator' => '=',
    'value' => array(
      'value' => '9',
      'min' => '',
      'max' => '',
    ),
  ),
  11 => array(
    'title' => 'October',
    'operator' => '=',
    'value' => array(
      'value' => '10',
      'min' => '',
      'max' => '',
    ),
  ),
  12 => array(
    'title' => 'November',
    'operator' => '=',
    'value' => array(
      'value' => '11',
      'min' => '',
      'max' => '',
    ),
  ),
);

/* Display: Data export */
$handler = $view->new_display('views_data_export', 'Data export', 'views_data_export_1');
$handler->display->display_options['pager']['type'] = 'none';
$handler->display->display_options['pager']['options']['offset'] = '0';
$handler->display->display_options['style_plugin'] = 'views_data_export_xml';
$handler->display->display_options['style_options']['provide_file'] = 1;
$handler->display->display_options['style_options']['filename'] = 'list_of_feasts.xml';
$handler->display->display_options['style_options']['parent_sort'] = 0;
$handler->display->display_options['style_options']['transform'] = 1;
$handler->display->display_options['style_options']['transform_type'] = 'underline';
$handler->display->display_options['style_options']['root_node'] = 'feasts';
$handler->display->display_options['style_options']['item_node'] = 'feast';
$handler->display->display_options['style_options']['no_entity_encode'] = array(
  'name' => 'name',
  'description' => 'description',
  'nothing' => 'nothing',
  'field_feastdate' => 'field_feastdate',
  'field_feast_code' => 'field_feast_code',
);
$handler->display->display_options['path'] = 'export-feasts';
$handler->display->display_options['displays'] = array(
  'page_1' => 'page_1',
  'default' => 0,
  'page_2' => 0,
);
$handler->display->display_options['sitename_title'] = 0;
