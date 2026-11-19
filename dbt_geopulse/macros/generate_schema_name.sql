{#
  By default dbt names a schema like  <default schema>_<custom schema>  (for example
  STAGING_MARTS). We want the exact names STAGING and MARTS, so we use the custom
  schema name directly.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema | trim }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
