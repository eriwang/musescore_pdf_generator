import argparse
import os

from drive_change_pdf_generator import run_drive_change_pdf_generator
from musescore.pdf_conversion import convert_to_pdf, convert_to_pdf_optimize_spatium, convert_with_manual_parts_to_pdf
from musescore.score import Score
from utils.os_path_utils import get_no_extension


def main():
    args = _parse_args()

    if args.mscz_to_convert is None:
        run_drive_change_pdf_generator()
    else:  # TODO: deduplicate with drive code, including helpers
        song_dir, song_basename = os.path.split(args.mscz_to_convert)
        song_name = get_no_extension(song_basename)
        score = Score.create_from_file(args.mscz_to_convert)

        if score.has_manual_parts():
            convert_with_manual_parts_to_pdf(score, song_dir, song_name)
            return

        _convert_to_pdf(score, f'{song_name}.gen.pdf', song_dir, optimize_spatium=False)
        if score.get_number_of_parts() == 1:
            return

        for part in score.generate_part_scores():
            _convert_to_pdf(part, f'{song_name} - {part.name}.gen.pdf', song_dir, optimize_spatium=True)


def _parse_args():
    parser = argparse.ArgumentParser(description='Convert mscz files on Drive to part PDF files, and sync to Drive.')
    parser.add_argument('--mscz-to-convert', help='Convert an mscz file on the local filesystem instead of drive.',
                        type=str)

    return parser.parse_args()


def _convert_to_pdf(score, output_filename, directory_name, optimize_spatium):
    output_filename = os.path.join(directory_name, output_filename)
    if optimize_spatium:
        convert_to_pdf_optimize_spatium(score, output_filename)
    else:
        convert_to_pdf(score, output_filename)


if __name__ == '__main__':
    main()
