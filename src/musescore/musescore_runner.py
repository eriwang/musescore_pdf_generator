import json
import subprocess
import os
import xml.etree.ElementTree as ET

from utils.os_path_utils import get_extension
from utils.tempfile_utils import scoped_named_temporary_file
from utils.xml_utils import create_node_with_text


# https://musescore.org/en/handbook/command-line-options
class MuseScore:
    binary_path = None

    @staticmethod
    def validate_binary():
        if MuseScore.binary_path is None:
            raise ValueError('MuseScore binary path never set')

        # Ideally, this would sanity test an actual command as well
        if not os.path.isfile(MuseScore.binary_path):
            raise RuntimeError(f'Non-existent MuseScore binary path {MuseScore.binary_path}')

    # TODO: ideally, filename generation is done in one central place (maybe even still in this class).
    @staticmethod
    def convert_mscz_to_pdf_with_manual_parts(song_name, mscz_filepath, out_dir):
        pdf_path_prefix = os.path.join(out_dir, song_name)
        musescore_job_params = [{
            'in': mscz_filepath,
            'out': [f'{pdf_path_prefix}.gen.pdf', [f'{pdf_path_prefix} - ', '.gen.pdf']]
        }]

        with scoped_named_temporary_file(content=json.dumps(musescore_job_params), suffix='.json') as job_json_filepath:
            subprocess.check_call([MuseScore.binary_path, '-j', job_json_filepath])

    @staticmethod
    def convert_to_pdf(src_filepath, out_filename, spatium=None):
        if get_extension(out_filename) != '.pdf':
            raise ValueError('Out filename must be of type .pdf')

        # For some reason, CLI MuseScore conversion doesn't apply style files to PDF conversion, but does to mscx (maybe
        # other types too). We get around this weirdness but making an intermediate mscx file that has styles.
        # Worth noting this might just be with the styles I'm working with (MM Rests, Spatium had some odd behavior as
        # well where it'd just shrink the notes and not adjust staff position).
        # TODO: On occasion Windows decides to throw a "[WinError 5] Access is denied" error, I'm not too sure why,
        #       seeing as it typically runs fine. Maybe there's some process call restrictions?
        style_file_text = MuseScore._create_style_file_text(spatium)
        with scoped_named_temporary_file(content=style_file_text, suffix='.mss') as style_filepath:
            with scoped_named_temporary_file(content='', suffix='.mscx') as mscx_with_styles:
                subprocess.check_call([MuseScore.binary_path, src_filepath, '-S', style_filepath, '-o',
                                       mscx_with_styles])
                subprocess.check_call([MuseScore.binary_path, mscx_with_styles, '-o', out_filename])

    @staticmethod
    def _create_style_file_text(spatium):
        style_file_root = ET.Element('museScore', version='3.01')
        style_node = ET.SubElement(style_file_root, 'Style')
        style_node.extend([
            create_node_with_text('createMultiMeasureRests', '1'),
            create_node_with_text('minEmptyMeasures', '2'),
            create_node_with_text('minMMRestWidth', '4'),
            create_node_with_text('multiMeasureRestMargin', '1.2')
        ])
        if spatium is not None:
            style_node.append(create_node_with_text('Spatium', str(spatium)))

        return ET.tostring(style_file_root)
