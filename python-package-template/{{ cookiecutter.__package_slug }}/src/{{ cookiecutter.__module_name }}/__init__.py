{#- The description is the package docstring. Up to 82 characters it stays one
    line ("""…""" within 88); longer, it moves below a summary line and wraps at
    88 without breaking a long word such as a URL. A final period keeps ruff's
    D415 quiet. -#}
{%- set description = cookiecutter.package_description | trim %}
{%- if description[-1:] not in [".", "?", "!"] %}{% set description = description ~ "." %}{% endif %}
{%- set summary = cookiecutter.package_name | trim %}
{%- if summary[-1:] not in [".", "?", "!"] %}{% set summary = summary ~ "." %}{% endif %}
{%- if description | length <= 82 -%}
"""{{ description }}"""
{%- else -%}
"""{{ summary }}

{{ description | wordwrap(width=88, break_long_words=false, break_on_hyphens=false) }}
"""
{%- endif %}

__version__ = "{{ cookiecutter.version }}"

__all__ = ["__version__"]
