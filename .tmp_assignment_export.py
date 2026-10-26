import ast
import json
import re
from pathlib import Path

import markdown
import nbformat
from nbconvert import HTMLExporter

folder = Path('AAI_501/M1')
path = next(p for p in folder.glob('Assignment_1.2*.ipynb') if not p.stem.endswith('_Question_2a'))
notebook = nbformat.read(path, as_version=4)
nbformat.validate(notebook)
for cell in notebook.cells:
    if cell.cell_type == 'code':
        ast.parse(cell.source)
assert not re.search(r'AIza[\w-]{25,}', json.dumps(notebook)), 'Potential embedded API key'

start = next(i for i, c in enumerate(notebook.cells) if c.source.startswith('# Question 2:'))
end = next(i for i, c in enumerate(notebook.cells) if c.source.startswith('## Question 2(b):'))
code_notebook = nbformat.v4.new_notebook(
    cells=[notebook.cells[0], *notebook.cells[start:end]],
    metadata=notebook.metadata,
)
code_path = folder / (path.stem + '_Question_2a.ipynb')
nbformat.write(code_notebook, code_path)
nbformat.validate(code_notebook)
html, _ = HTMLExporter().from_notebook_node(code_notebook)
code_path.with_suffix('.html').write_text(html, encoding='utf-8')

written = [
    c.source for c in notebook.cells
    if c.cell_type == 'markdown' and not c.source.startswith(('# Question 2:', '### Question 2(a):'))
]
written.insert(1, '**Submission guide:** This PDF answers Questions 1(a), 1(b), 2(b), and 2(c). Question 2(a), including code and its recorded execution outcome, is provided in the separate HTML notebook export.')
written.append('## References\n\n- [LlamaIndex agents](https://developers.llamaindex.ai/python/framework/understanding/putting_it_all_together/agents/)\n- [Google Gemini with LlamaIndex](https://ai.google.dev/gemini-api/docs/llama-index)\n- [RSS Guard: standard feeds and OPML import](https://rssguard.readthedocs.io/en/stable/services/standard.html)')
written_path = folder / (path.stem + '_Written_Responses.md')
written_text = '\n\n'.join(written)
written_path.write_text(written_text, encoding='utf-8')
style = '''body{font-family:Arial,sans-serif;font-size:10pt;line-height:1.4;color:#172337}
h1{font-size:21pt;color:#173d60}h2{font-size:15pt;color:#173d60;margin-top:24px}h3{font-size:12pt}
table{break-inside:avoid;border-collapse:collapse;width:100%;font-size:9pt}th,td{border:1px solid #bac7d4;padding:7px;vertical-align:top}
th{background:#eaf0f6}pre{white-space:pre-wrap;font-size:8pt}a{color:#205c8c;overflow-wrap:anywhere}
tr{break-inside:avoid}h1,h2,h3{break-after:avoid}@page{size:Letter;margin:0.65in}'''
body = markdown.markdown(written_text, extensions=['tables', 'fenced_code'])
written_path.with_suffix('.html').write_text(
    '<!doctype html><html><head><meta charset="utf-8"><title>Assignment 1.2 - Francisco Gutierrez</title>'
    '<style>' + style + '</style></head><body>' + body + '</body></html>', encoding='utf-8',
)
print('Validated notebooks and syntax; regenerated code HTML and written responses. No cells executed.')
