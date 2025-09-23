(struct_specifier
  name: (type_identifier) @name.definition.class
  body: (_)) @definition.class

(declaration
  type: (union_specifier
    name: (type_identifier) @name.definition.class)) @definition.class

(class_specifier
  name: (type_identifier) @name.definition.class) @definition.class

(field_declaration
  declarator: (function_declarator
    declarator: (field_identifier) @name.definition.function)) @definition.function

(function_definition
  declarator: (function_declarator
    declarator: (identifier) @name.definition.function)) @definition.function

(function_definition
  declarator: (function_declarator
    declarator: (field_identifier) @name.definition.function)) @definition.function

(function_definition
  declarator: (function_declarator
    declarator: (qualified_identifier
      scope: (namespace_identifier) @scope
      name: (identifier) @name.definition.function))) @definition.function

(type_definition
  declarator: (type_identifier) @name.definition.type) @definition.type

(enum_specifier
  name: (type_identifier) @name.definition.type) @definition.type

(call_expression
  function: [
    (identifier) @name.reference.call
    (field_expression
      field: (field_identifier) @name.reference.call)
  ]) @reference.call