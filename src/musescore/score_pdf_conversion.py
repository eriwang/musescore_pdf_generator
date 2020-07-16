from PyPDF2 import PdfFileReader

from musescore.musescore_runner import MuseScore
from utils.tempfile_utils import scoped_named_temporary_file


def convert_score_to_pdf_optimize_spatium(score, out_filename):
    _MINIMUM_SPATIUM = 1.5
    _MUSESCORE_DEFAULT_SPATIUM = 1.76389
    _SPATIUM_INCREMENT = 0.025

    spatium = _MINIMUM_SPATIUM
    minimum_pdf_num_pages = None
    while spatium <= _MUSESCORE_DEFAULT_SPATIUM:
        _convert_score_to_pdf_with_spatium(score, out_filename, spatium)
        pdf_num_pages = PdfFileReader(out_filename).getNumPages()
        if minimum_pdf_num_pages is None:
            minimum_pdf_num_pages = pdf_num_pages
        elif pdf_num_pages > minimum_pdf_num_pages:
            _convert_score_to_pdf_with_spatium(score, out_filename, spatium - _SPATIUM_INCREMENT)
            break

        spatium += _SPATIUM_INCREMENT


def _convert_score_to_pdf_with_spatium(score, out_filename, spatium):
    with scoped_named_temporary_file(content=score.get_mscx_as_string(), suffix='.mscx') as mscx:
        MuseScore().convert_to_pdf(mscx, out_filename, spatium)
