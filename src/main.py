import argparse
import json
import os

from drive_change_pdf_generator import run_drive_change_pdf_generator
from musescore.musescore_runner import MuseScore
from musescore.pdf_conversion import convert_mscz_to_pdfs
from utils.os_path_utils import get_no_extension


def main():
    args = _parse_args()

    with open(args.config) as f:
        config_dict = json.load(f)

    MuseScore.binary_path = config_dict['musescore_binary']
    MuseScore.validate_binary()

    if args.mscz_to_convert is not None:
        song_dir, song_basename = os.path.split(args.mscz_to_convert)
        convert_mscz_to_pdfs(
            mscz_filename=args.mscz_to_convert,
            output_directory=song_dir,
            song_name=get_no_extension(song_basename))
        return

    run_drive_change_pdf_generator(config_dict['drive_folder_id'])


def _parse_args():
    _DEFAULT_CONFIG_FILENAME = 'config.json'
    parser = argparse.ArgumentParser(description='Convert mscz files on Drive to part PDF files, and sync to Drive.')
    parser.add_argument('--config',
                        help=f'Configuration file. If not specified, looks for a file named '
                             f'"{_DEFAULT_CONFIG_FILENAME}" in the working directory.',
                        type=str, default=_DEFAULT_CONFIG_FILENAME)
    parser.add_argument('--mscz-to-convert', help='Convert an mscz file on the local filesystem instead of drive.',
                        type=str)

    return parser.parse_args()


if __name__ == '__main__':
    main()
