import os
import tempfile

from drive.drive import Drive
from musescore.score import Score
from musescore.pdf_conversion import convert_to_pdf, convert_to_pdf_optimize_spatium, convert_with_manual_parts_to_pdf
from utils.os_path_utils import get_no_extension, get_extension

_TEST_FOLDER_ROOT_ID = '11HTp4Y8liv9Oc0Sof0bxvlsGSLmQAvl4'

# App flow:
# - Every so often, do a traversal of the "root" folder and store all musescore file IDs
#   - If there's any new ones, generate PDFs for them.
#   - Fine to ignore old ones, just stop generating for them
# - Listen to changes API. If a file ID appears that's in the musescore file ID list, regen
# - Note that I should probably clear the existing PDFs if I know I'm going to regen (e.g. if I change part names)
#   - Could be an option?
#   - In any case apparently duplicate filenames are allowed for some reason???? Need to delete the ones that exit

# TODO: listen to changes
#       make it just run forever, listening to changes, refreshing them, and generating
def main():
    d = Drive.create_authenticate_and_start()
    files = d.recursively_search_directory(_TEST_FOLDER_ROOT_ID)
    for f in files:
        is_musescore_file = (f.mime_type == 'application/x-musescore') or \
                            (get_extension(f.name) == '.mscx' and f.mime_type == 'text/xml')
        if not is_musescore_file:
            continue

        if len(f.parents) != 1:
            raise ValueError(f'File id {f.id} name {f.name} does not have exactly 1 parent')

        with d.open_as_temporary_named_file(f.id, suffix=get_extension(f.name)) as musescore_file:
            _convert_opened_drive_file_to_pdf_and_upload(d, musescore_file,
                                                         song_name=get_no_extension(f.name),
                                                         upload_dir=f.parents[0])


def _convert_opened_drive_file_to_pdf_and_upload(drive, musescore_file, song_name, upload_dir):
    score = Score.create_from_file(musescore_file)
    score_output_filename = f'{song_name}.gen.pdf'

    if score.has_manual_parts():
        _convert_with_manual_parts_to_pdf_and_upload(drive, score, upload_dir, song_name)
        return

    # I'm choosing not to optimize the spatium here because this is what the user sees in MuseScore. Optimizing
    # spatium is just for the parts that the users don't see (which is a tad arbitrarily decided, and should
    # probably be an option).
    _convert_to_pdf_and_upload(drive, score, score_output_filename, upload_dir, optimize_spatium=False)
    if score.get_number_of_parts() == 1:
        return

    for part in score.generate_part_scores():
        _convert_to_pdf_and_upload(drive, part, f'{song_name} - {part.name}.gen.pdf', upload_dir,
                                   optimize_spatium=True)


def _convert_with_manual_parts_to_pdf_and_upload(drive, score, upload_dir, song_name):
    with tempfile.TemporaryDirectory() as tempdir:
        convert_with_manual_parts_to_pdf(score, tempdir, song_name)
        for gen_file in os.listdir(tempdir):
            drive.upload_or_update_file(os.path.join(tempdir, gen_file), upload_dir)


def _convert_to_pdf_and_upload(drive, score, output_filename, upload_dir, optimize_spatium):
    with tempfile.TemporaryDirectory() as tempdir:
        output_filename = os.path.join(tempdir, output_filename)
        if optimize_spatium:
            convert_to_pdf_optimize_spatium(score, output_filename)
        else:
            convert_to_pdf(score, output_filename)

        drive.upload_or_update_file(output_filename, upload_dir)


if __name__ == '__main__':
    main()
