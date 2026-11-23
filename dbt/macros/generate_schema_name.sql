{#
  By default dbt names custom schemas "<target schema>_<custom schema>",
  e.g. analytics_staging. This keeps the names simple: staging and marts.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}