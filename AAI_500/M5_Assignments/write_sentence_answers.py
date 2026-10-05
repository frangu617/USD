"""Make executed query interpretations and evaluation permanent Markdown cells."""
from pathlib import Path
import nbformat

def add_written_answers(notebook):
    notebook.cells = [cell for cell in notebook.cells
                      if not cell.metadata.get('written_answer_from_results')]
    new_cells = []
    for cell in notebook.cells:
        new_cells.append(cell)
        if cell.cell_type != 'code':
            continue
        is_queries = 'query_results = []' in cell.source
        is_classifier = 'baseline_accuracy = accuracy_score' in cell.source
        if not (is_queries or is_classifier):
            continue
        paragraphs = []
        for output in cell.outputs:
            if output.output_type in ['display_data', 'execute_result']:
                value = output.get('data', {}).get('text/markdown')
                if value:
                    paragraphs.append(value)
        if not paragraphs:
            raise ValueError('Execute the notebook before materializing written answers.')
        title = '### Answers to queries a-e' if is_queries else '### Classifier results and interpretation'
        if is_queries:
            paragraphs.append('In query e, the added High Oldpeak evidence lowers the estimate slightly rather than increasing it. The model does not impose monotonic risk effects, and only 23 patients have this complete evidence combination; this result should therefore be interpreted in light of the learned dependencies, smoothing, and limited subgroup support.')
        answer = nbformat.v4.new_markdown_cell(title + '\n\n' + '\n\n'.join(paragraphs))
        answer.metadata['written_answer_from_results'] = True
        new_cells.append(answer)
    notebook.cells = new_cells
    return notebook

def main():
    base = Path(__file__).resolve().parent
    path = base / 'AAI_500_M5_Assignment_Completed.ipynb'
    notebook = add_written_answers(nbformat.read(path, as_version=4))
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    paragraphs = [cell.source for cell in notebook.cells if cell.cell_type == 'markdown'
                  and (cell.metadata.get('written_answer_from_results') or
                       cell.source.startswith(('### EDA interpretation', '### Final structure choice', '## 5. Discussion')))]
    (base / 'Assignment_5_1_Written_Answers.md').write_text(
        '# Assignment 5.1: Written answers\n\n'
        'These answers describe the saved run in `AAI_500_M5_Assignment_Completed.ipynb`.\n\n'
        + '\n\n'.join(paragraphs), encoding='utf-8')
    print('Added permanent query and classifier answer cells; exported all five written sections.')

if __name__ == '__main__':
    main()
