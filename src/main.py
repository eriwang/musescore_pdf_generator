import argparse
import os

from drive_change_pdf_generator import run_drive_change_pdf_generator
from musescore.pdf_conversion import convert_mscz_to_pdfs
from utils.os_path_utils import get_no_extension


def main():
    args = _parse_args()

    if args.mscz_to_convert is None:
        run_drive_change_pdf_generator()
    else:
        song_dir, song_basename = os.path.split(args.mscz_to_convert)
        convert_mscz_to_pdfs(
            mscz_filename=args.mscz_to_convert,
            output_directory=song_dir,
            song_name=get_no_extension(song_basename))


def _parse_args():
    parser = argparse.ArgumentParser(description='Convert mscz files on Drive to part PDF files, and sync to Drive.')
    parser.add_argument('--mscz-to-convert', help='Convert an mscz file on the local filesystem instead of drive.',
                        type=str)

    return parser.parse_args()


if __name__ == '__main__':
    main()
