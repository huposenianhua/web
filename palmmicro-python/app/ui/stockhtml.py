"""HTML element generation utilities.

Translated from PHP ui/htmlelement.php.
Provides helper functions for generating HTML elements.
"""


STOCK_DISP_ASHARES = 'A股'
STOCK_DISP_BSHARES = 'B股'
STOCK_DISP_CALIBRATION = '校准'
STOCK_DISP_CHANGE = '涨幅'
STOCK_DISP_EST = 'EST'
STOCK_DISP_FAIR = '参考'
STOCK_DISP_HEDGE = '对冲值'
STOCK_DISP_HIGH = '最高'
STOCK_DISP_HOLDING = '持仓'
STOCK_DISP_HSHARES = 'H股'
STOCK_DISP_LOW = '最低'
STOCK_DISP_NETVALUE = '净值'
STOCK_DISP_OFFICIAL = '官方'
STOCK_DISP_OPEN = '开盘'
STOCK_DISP_ORDER = '申购'
STOCK_DISP_POSITION = '仓位'
STOCK_DISP_PREMIUM = '溢价'
STOCK_DISP_PRICE = '价格'
STOCK_DISP_PROFIT = '盈利'
STOCK_DISP_QUANTITY = '数量'
STOCK_DISP_RATIO = '比价'
STOCK_DISP_REALTIME = '实时'
STOCK_DISP_REMARK = '备注'
STOCK_DISP_SYMBOL = '代码'
STOCK_DISP_TURNOVER = '换手'


def get_content_type() -> str:
    """Get HTML content type meta tag."""
    return '<meta http-equiv="content-type" content="text/html; charset=UTF-8">'


def get_double_quotes(text: str) -> str:
    """Wrap text in double quotes."""
    return f'"{text}"'


def get_img_element(path: str, alt_text: str) -> str:
    """Generate img element."""
    return f'<img src="{path}" alt={get_double_quotes(alt_text)} />'


def get_html_newline() -> str:
    """Get HTML line break."""
    return '<br />'


def get_html_space() -> str:
    """Get HTML non-breaking space."""
    return '&nbsp;'


def get_html_element(content: str, tag: str = 'p', attributes: dict = None) -> str:
    """Generate HTML element with optional attributes."""
    attr_str = ''
    if attributes:
        for attr, value in attributes.items():
            attr_str += f' {attr}'
            if value is not False:
                attr_str += f'={value}'
    
    return f"<{tag}{attr_str}>{content}</{tag}>"


def get_empty_element() -> str:
    """Generate empty element."""
    return get_html_element(get_html_space())


def get_link_element(content: str, href: str, extra_attributes: dict = None) -> str:
    """Generate anchor element."""
    attrs = {'href': get_double_quotes(href)}
    if extra_attributes:
        attrs.update(extra_attributes)
    return get_html_element(content, 'a', attrs)


def get_bold_element(content: str) -> str:
    """Generate bold element."""
    return get_html_element(content, 'b')


def get_underline_element(content: str) -> str:
    """Generate underline element."""
    return get_html_element(content, 'u')


def get_font_element(content: str, color: str = 'red', style: str = None) -> str:
    """Generate font element with color and optional style."""
    attrs = {'color': color}
    if style:
        attrs['style'] = get_double_quotes(style)
    return get_html_element(content, 'font', attrs)


def get_info_element(content: str) -> str:
    """Generate info element (blue text)."""
    return get_font_element(content, 'blue')


def get_remark_element(content: str) -> str:
    """Generate remark element (green text)."""
    return get_font_element(content, 'green')


def get_quote_element(content: str, style: str = None) -> str:
    """Generate quote element (gray text)."""
    return get_font_element(content, 'gray', style)


def get_blockquote_element(content: str) -> str:
    """Generate blockquote element."""
    return get_html_element(get_quote_element(content), 'blockquote')


def get_code_element(content: str) -> str:
    """Generate code element (olive text)."""
    return get_html_element(get_font_element(content, 'olive'), 'code')


def get_head_element(content: str) -> str:
    """Generate heading element."""
    return get_html_element(content, 'h3')


def get_list_element(items: list, ordered: bool = True) -> str:
    """Generate ordered or unordered list."""
    list_tag = 'ol' if ordered else 'ul'
    items_html = ''.join(get_html_element(item, 'li') for item in items)
    return get_html_element(items_html, list_tag)


def _set_html_element(name: str) -> str:
    """Generate attribute assignment string."""
    return f'{name}="{name}"'


def html_element_selected() -> str:
    """Generate selected attribute."""
    return _set_html_element('selected')


def html_element_disabled() -> str:
    """Generate disabled attribute."""
    return _set_html_element('disabled')


def html_element_readonly() -> str:
    """Generate readonly attribute with gray background."""
    return f'{_set_html_element("readonly")} style="background:#CCCCCC"'


def html_get_option(options: dict, selected_value: str = None) -> str:
    """Generate option elements for select."""
    html = ''
    for key, val in options.items():
        selected = f' {html_element_selected()}' if val == selected_value else ''
        html += get_html_element(val, 'OPTION', {'value': f'{key}{selected}'})
    return html


def html_get_js_array(data: dict) -> str:
    """Generate JavaScript object literal string."""
    items = [f'{key}:"{val}"' for key, val in data.items()]
    return ', '.join(items)


def convert_to_html_display(text: str) -> str:
    """Convert plain text to HTML display format."""
    text = text.replace(' ', get_html_space())
    return text.replace('\n', get_html_newline())