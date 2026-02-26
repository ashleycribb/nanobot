from nanobot.utils.markdown import markdown_to_telegram_html


def test_plain_text():
    assert markdown_to_telegram_html("hello world") == "hello world"
    assert markdown_to_telegram_html("") == ""

def test_bold():
    assert markdown_to_telegram_html("**bold**") == "<b>bold</b>"
    assert markdown_to_telegram_html("__bold__") == "<b>bold</b>"

def test_italic():
    assert markdown_to_telegram_html("_italic_") == "<i>italic</i>"
    assert markdown_to_telegram_html("word_with_underscore") == "word_with_underscore"
    assert markdown_to_telegram_html("_italic_ word") == "<i>italic</i> word"

def test_strikethrough():
    assert markdown_to_telegram_html("~~strike~~") == "<s>strike</s>"

def test_inline_code():
    assert markdown_to_telegram_html("`code`") == "<code>code</code>"
    # Special characters inside code should be escaped
    assert markdown_to_telegram_html("`<b>bold</b>`") == "<code>&lt;b&gt;bold&lt;/b&gt;</code>"

def test_code_block():
    md = "```python\nprint('hello')\n```"
    expected = "<pre><code>print('hello')\n</code></pre>"
    assert markdown_to_telegram_html(md) == expected

    # Special characters inside code block should be escaped
    md_special = "```\n<script>\n```"
    expected_special = "<pre><code>&lt;script&gt;\n</code></pre>"
    assert markdown_to_telegram_html(md_special) == expected_special

def test_links():
    assert markdown_to_telegram_html("[Google](https://google.com)") == '<a href="https://google.com">Google</a>'

    # Complex link text
    assert markdown_to_telegram_html("[Link with spaces](url)") == '<a href="url">Link with spaces</a>'

def test_headers():
    assert markdown_to_telegram_html("# Header 1") == "Header 1"
    assert markdown_to_telegram_html("## Header 2") == "Header 2"

def test_lists():
    assert markdown_to_telegram_html("- item 1") == "• item 1"
    assert markdown_to_telegram_html("* item 2") == "• item 2"

def test_html_escaping():
    assert markdown_to_telegram_html("Normal < Tag") == "Normal &lt; Tag"
    assert markdown_to_telegram_html("A & B") == "A &amp; B"

def test_nested_formatting():
    # Link inside bold - note: the current regex logic processes links BEFORE bold
    # So **[link](url)** -> **<a href="url">link</a>** -> <b><a href="url">link</a></b>
    assert markdown_to_telegram_html("**[link](url)**") == '<b><a href="url">link</a></b>'

    # Bold inside link?
    # [**bold**](url) -> <a href="url">**bold**</a> -> <a href="url"><b>bold</b></a>
    # Let's verify what the code does.
    # Step 6: Links [text](url) -> <a href="url">text</a>
    # Step 7: Bold **text** -> <b>text</b>
    # So yes, [**bold**](url) becomes <a href="url">**bold**</a> then <a href="url"><b>bold</b></a>
    assert markdown_to_telegram_html("[**bold**](url)") == '<a href="url"><b>bold</b></a>'

def test_blockquote():
    assert markdown_to_telegram_html("> quote") == "quote"

def test_mixed_content():
    text = """# Title
Hello **world**!
Check `code` and [link](url).
- Item 1
- Item 2
"""
    expected = """Title
Hello <b>world</b>!
Check <code>code</code> and <a href="url">link</a>.
• Item 1
• Item 2
"""
    assert markdown_to_telegram_html(text) == expected
