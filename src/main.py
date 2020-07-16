import os

from PyPDF2 import PdfFileReader

from musescore.musescore_runner import MuseScore
from musescore.score import Score
from utils.tempfile_utils import scoped_named_temporary_file


def main():
    out_path = 'C:/Users/johne/Desktop/musescore_pdf_gen_testing/'
    gurenge_file = 'C:/Users/johne/Desktop/connect_trio_no_parts.mscz'
    score = Score.create_from_file(gurenge_file)

    _convert_score_to_pdf_optimize_spatium(score, os.path.join(out_path, 'Gurenge.pdf'))
    for part in score.generate_part_scores():
        out_filename = os.path.join(out_path, f'Gurenge - {part.name}.pdf')
        _convert_score_to_pdf_optimize_spatium(part, out_filename)


def _convert_score_to_pdf_optimize_spatium(score, out_filename):
    _MINIMUM_SPATIUM = 1.5
    _MUSESCORE_DEFAULT_SPATIUM = 1.76389
    _SPATIUM_INCREMENT = 0.025

    spatium = _MINIMUM_SPATIUM
    minimum_pdf_num_pages = None
    while spatium <= _MUSESCORE_DEFAULT_SPATIUM:
        _convert_score_to_pdf_with_spatium(score, spatium, out_filename)
        pdf_num_pages = PdfFileReader(out_filename).getNumPages()
        if minimum_pdf_num_pages is None:
            minimum_pdf_num_pages = pdf_num_pages
        elif pdf_num_pages > minimum_pdf_num_pages:
            _convert_score_to_pdf_with_spatium(score, spatium - _SPATIUM_INCREMENT, out_filename)
            break

        spatium += _SPATIUM_INCREMENT


def _convert_score_to_pdf_with_spatium(score, spatium, out_filename):
    score.set_spatium(spatium)
    with scoped_named_temporary_file(content=score.get_mscx_as_string(), suffix='.mscx') as mscx:
        MuseScore().convert_to_pdf(mscx, out_filename)


if __name__ == '__main__':
    main()
