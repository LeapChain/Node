REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': ('rest_framework.parsers.JSONParser',),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'EXCEPTION_HANDLER': 'node.core.exceptions.custom_exception_handler',
}
