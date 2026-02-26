from nanobot.utils.markdown import markdown_to_telegram_html


def test_markdown_to_telegram_html_empty():
    assert markdown_to_telegram_html("") == ""
    assert markdown_to_telegram_html(None) == ""

def test_markdown_to_telegram_html_escaping():
    assert markdown_to_telegram_html("a & b < c > d") == "a &amp; b &lt; c &gt; d"

def test_markdown_to_telegram_html_bold():
    assert markdown_to_telegram_html("**bold**") == "<b>bold</b>"
    assert markdown_to_telegram_html("__bold__") == "<b>bold</b>"

def test_markdown_to_telegram_html_italic():
    assert markdown_to_telegram_html("_italic_") == "<i>italic</i>"
    # Ensure it doesn't match inside words
    assert markdown_to_telegram_html("some_var_name") == "some_var_name"

def test_markdown_to_telegram_html_strikethrough():
    assert markdown_to_telegram_html("~~strike~~") == "<s>strike</s>"

def test_markdown_to_telegram_html_links():
    assert markdown_to_telegram_html("[link](http://example.com)") == '<a href="http://example.com">link</a>'

def test_markdown_to_telegram_html_headers():
    assert markdown_to_telegram_html("# Header 1") == "Header 1"
    assert markdown_to_telegram_html("### Header 3") == "Header 3"

def test_markdown_to_telegram_html_blockquotes():
    assert markdown_to_telegram_html("> quote") == "quote"

def test_markdown_to_telegram_html_bullets():
    assert markdown_to_telegram_html("- item 1\n* item 2") == "• item 1\n• item 2"

def test_markdown_to_telegram_html_inline_code():
    assert markdown_to_telegram_html("`code`") == "<code>code</code>"
    # Content inside inline code should be escaped
    assert markdown_to_telegram_html("`<tag>&`") == "<code>&lt;tag&gt;&amp;</code>"

def test_markdown_to_telegram_html_code_block():
    code_block = """```python
print("hello")
```"""
    expected = "<pre><code>print(\"hello\")\n</code></pre>"
    assert markdown_to_telegram_html(code_block) == expected

def test_markdown_to_telegram_html_code_block_escaping():
    code_block = """```html
<tag>&</tag>
```"""
    expected = "<pre><code>&lt;tag&gt;&amp;&lt;/tag&gt;\n</code></pre>"
    assert markdown_to_telegram_html(code_block) == expected

def test_markdown_to_telegram_html_nested():
    # Bold inside link text
    assert markdown_to_telegram_html("[**bold link**](http://example.com)") == '<a href="http://example.com"><b>bold link</b></a>'

    # Complex case
    input_text = """# Title
- Item with **bold**
- Item with `code`
> Quote with _italic_
[Link](url)
"""
    expected = """Title
• Item with <b>bold</b>
• Item with <code>code</code>
Quote with <i>italic</i>
<a href="url">Link</a>
"""
    assert markdown_to_telegram_html(input_text) == expected
