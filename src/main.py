import os

from drive.drive import Drive
from musescore.score import Score
from musescore.score_pdf_conversion import convert_score_to_pdf_optimize_spatium

_TEST_FOLDER_ROOT_ID = '11HTp4Y8liv9Oc0Sof0bxvlsGSLmQAvl4'

# App flow:
# - Every so often, do a traversal of the "root" folder and store all musescore file IDs
#   - If there's any new ones, generate PDFs for them.
#   - Fine to ignore old ones, just stop generating for them
# - Listen to changes API. If a file ID appears that's in the musescore file ID list, regen

# TODO: next up, take a file through the whole "download gen upload to dir" pipeline,
#       then listen to changes
#       then make it just run forever, listening to changes, refreshing them, and generating
def main():
    d = Drive.create_authenticate_and_start()
    files = d.recursively_search_directory(_TEST_FOLDER_ROOT_ID)
    print([f for f in files if _drive_file_is_musescore_file(f)])


def _convert_file_to_pdf(filename, out_path, song_name):
    score = Score.create_from_file(filename)

    convert_score_to_pdf_optimize_spatium(score, os.path.join(out_path, f'{song_name}.pdf'))
    for part in score.generate_part_scores():
        out_filename = os.path.join(out_path, f'{song_name} - {part.name}.pdf')
        convert_score_to_pdf_optimize_spatium(part, out_filename)


def _drive_file_is_musescore_file(drive_file):
    extension = os.path.splitext(drive_file.name)[1]
    return (drive_file.mime_type == 'application/x-musescore') or \
           (extension == '.mscx' and drive_file.mime_type == 'text/xml')


if __name__ == '__main__':
    main()
