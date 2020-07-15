import xml.etree.ElementTree as ET
import json
import subprocess
import os
import platform

from utils.tempfile_utils import temporary_named_file
from utils.xml_utils import create_node_with_text

# TODO: should be default install location, and if user installs it elsewhere they need to tell the app
_MUSESCORE_BINARY = 'C:/Program Files/MuseScore 3/bin/MuseScore3.exe' if platform.system() == 'Windows' else \
                    '/mnt/c/Program Files/MuseScore 3/bin/MuseScore3.exe'
_MINIMUM_SPATIUM = 1.5
_SPATIUM_INCREMENT = 0.025

# https://musescore.org/en/handbook/command-line-options
class MuseScore:
    def __init__(self, binary_path=_MUSESCORE_BINARY):
        if not os.path.isfile(binary_path):
            raise ValueError(f'Could not find a file at MuseScore binary location: {binary_path}')

        self._binary_path = binary_path

    def convert_mscz_to_pdf_with_manual_parts(self, mscz_filepath, out_dir):
        pdf_path_prefix = os.path.join(out_dir, MuseScore._get_pdf_prefix(mscz_filepath))
        musescore_job_params = [{
            'in': mscz_filepath,
            'out': [f'{pdf_path_prefix}.pdf', [f'{pdf_path_prefix} - ', '.pdf']]
        }]

        with temporary_named_file(content=json.dumps(musescore_job_params), suffix='.json') as job_json_filepath:
            subprocess.check_call([self._binary_path, '-j', job_json_filepath])

    def convert_to_pdf(self, src_filepath, out_filename):
        if os.path.splitext(out_filename)[1] != '.pdf':
            raise ValueError('Out filename must be of type .pdf')

        with temporary_named_file(content=_create_style_file_text(_MINIMUM_SPATIUM), suffix='.mss') as style_file:
            subprocess.check_call([self._binary_path, src_filepath, '-o', out_filename, '-S', style_file])

    @staticmethod
    def _get_pdf_prefix(src_filepath):
        return os.path.splitext(os.path.basename(src_filepath))[0]


def _create_style_file_text(spatium):
    style_file_root = ET.Element('museScore', version='3.01')
    style_node = ET.SubElement(style_file_root, 'Style')
    style_node.extend([
        create_node_with_text('createMultimeasureRests', '1'),
        create_node_with_text('minEmptyMeasures', '2'),
        create_node_with_text('minMMRestWidth', '4'),
        create_node_with_text('multiMeasureRestMargin', '1.2'),
        create_node_with_text('Spatium', str(spatium))
    ])

    return ET.tostring(style_file_root)
