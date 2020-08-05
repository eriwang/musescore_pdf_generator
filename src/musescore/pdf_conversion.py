from PyPDF2 import PdfFileReader

from musescore.musescore_runner import MuseScore
from utils.tempfile_utils import scoped_named_temporary_file


def convert_to_pdf(score, out_filepath, spatium=None):
    with scoped_named_temporary_file(content=score.get_mscx_as_string(), suffix='.mscx') as mscx:
        MuseScore().convert_to_pdf(mscx, out_filepath, spatium)


# TODO: if default spatium and min spatium have same number of pages, can just return right away.
#       Probably do a binary search for optimal spatium
def convert_to_pdf_optimize_spatium(score, out_filepath):
    _MINIMUM_SPATIUM = 1.5
    _MUSESCORE_DEFAULT_SPATIUM = 1.76389
    _SPATIUM_INCREMENT = 0.025

    spatium = _MINIMUM_SPATIUM
    minimum_pdf_num_pages = None
    while spatium <= _MUSESCORE_DEFAULT_SPATIUM:
        convert_to_pdf(score, out_filepath, spatium)
        pdf_num_pages = PdfFileReader(out_filepath).getNumPages()
        if minimum_pdf_num_pages is None:
            minimum_pdf_num_pages = pdf_num_pages
        elif pdf_num_pages > minimum_pdf_num_pages:
            convert_to_pdf(score, out_filepath, spatium - _SPATIUM_INCREMENT)
            break

        spatium += _SPATIUM_INCREMENT


def convert_with_manual_parts_to_pdf(score, out_dir, song_name):
    with scoped_named_temporary_file(content=score.get_mscx_as_string(), suffix='.mscx') as mscx:
        MuseScore().convert_mscz_to_pdf_with_manual_parts(song_name, mscx, out_dir)
