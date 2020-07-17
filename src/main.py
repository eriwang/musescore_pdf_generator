import os
import tempfile
import time

from drive.drive import Drive
from musescore.score import Score
from musescore.pdf_conversion import convert_to_pdf, convert_to_pdf_optimize_spatium, convert_with_manual_parts_to_pdf
from utils.os_path_utils import get_no_extension, get_extension

_TEST_FOLDER_ROOT_ID = '11HTp4Y8liv9Oc0Sof0bxvlsGSLmQAvl4'


def main():
    d = Drive.create_authenticate_and_start()

    listening_file_ids = _refresh_listening_file_id_index_and_regen(d, _TEST_FOLDER_ROOT_ID)
    counter = 1
    while True:
        if counter % 10 == 0:
            listening_file_ids = _refresh_listening_file_id_index_and_regen(d, _TEST_FOLDER_ROOT_ID)

        for c in d.get_changes():
            if c.id not in listening_file_ids:
                continue
            if c.removed:
                listening_file_ids.remove(c.id)
                continue

            # You can save an API query by caching the results of the change and using it here, but this makes the code
            # a (tiny bit) easier to write.
            _generate_pdfs_for_file_id_if_needed(d, c.id)

        counter += 1
        time.sleep(5)


def _refresh_listening_file_id_index_and_regen(drive, root):
    listening_file_ids = {f.id for f in drive.recursively_search_directory(root)
                          if _is_processable_musescore_file(f)}
    for file_id in listening_file_ids:
        _generate_pdfs_for_file_id_if_needed(drive, file_id)

    return listening_file_ids


def _generate_pdfs_for_file_id_if_needed(drive, file_id):
    drive_file = drive.get_file_metadata(file_id)
    assert _is_processable_musescore_file(drive_file)

    gen_pdf_drive_files = [item for item in drive.list_directory(drive_file.parents[0])
                           if item.name.endswith('.gen.pdf')]
    min_gen_pdf_modified_datetime = min([f.modified_datetime for f in gen_pdf_drive_files])
    if drive_file.modified_datetime < min_gen_pdf_modified_datetime:
        print(f'pdfs up to date for {drive_file.name}')
        return

    print(f'need to update pdfs for {drive_file.name}')

    untouched_gen_pdf_ids = {f.id for f in gen_pdf_drive_files}
    with drive.open_as_temporary_named_file(drive_file.id, suffix=get_extension(drive_file.name)) as musescore_file:
        gen_pdf_ids = _convert_opened_drive_file_to_pdf_and_upload(
            drive,
            musescore_file,
            song_name=get_no_extension(drive_file.name),
            upload_dir=drive_file.parents[0])
        print(gen_pdf_ids)
        for gen_pdf_id in gen_pdf_ids:
            if gen_pdf_id in untouched_gen_pdf_ids:
                untouched_gen_pdf_ids.remove(gen_pdf_id)

    print(f'Following ids remain: {untouched_gen_pdf_ids}')
    for trash_id in untouched_gen_pdf_ids:
        drive.move_file_to_trash(trash_id)


def _convert_opened_drive_file_to_pdf_and_upload(drive, musescore_file, song_name, upload_dir):
    score = Score.create_from_file(musescore_file)
    score_output_filename = f'{song_name}.gen.pdf'

    if score.has_manual_parts():
        return _convert_with_manual_parts_to_pdf_and_upload(drive, score, upload_dir, song_name)

    # I'm choosing not to optimize the spatium here because this is what the user sees in MuseScore. Optimizing
    # spatium is just for the parts that the users don't see (which is a tad arbitrarily decided, and should
    # probably be an option).
    uploaded_file_ids = []
    uploaded_file_ids.append(_convert_to_pdf_and_upload(
        drive,
        score,
        score_output_filename,
        upload_dir,
        optimize_spatium=False))
    if score.get_number_of_parts() == 1:
        return uploaded_file_ids

    for part in score.generate_part_scores():
        uploaded_file_ids.append(_convert_to_pdf_and_upload(
            drive,
            part,
            f'{song_name} - {part.name}.gen.pdf',
            upload_dir,
            optimize_spatium=True))

    return uploaded_file_ids


def _convert_with_manual_parts_to_pdf_and_upload(drive, score, upload_dir, song_name):
    ids = []
    with tempfile.TemporaryDirectory() as tempdir:
        convert_with_manual_parts_to_pdf(score, tempdir, song_name)
        for gen_file in os.listdir(tempdir):
            ids.append(drive.upload_or_update_file(os.path.join(tempdir, gen_file), upload_dir))
    return ids


def _convert_to_pdf_and_upload(drive, score, output_filename, upload_dir, optimize_spatium):
    print(f'converting {output_filename}')
    with tempfile.TemporaryDirectory() as tempdir:
        output_filename = os.path.join(tempdir, output_filename)
        if optimize_spatium:
            convert_to_pdf_optimize_spatium(score, output_filename)
        else:
            convert_to_pdf(score, output_filename)

        return drive.upload_or_update_file(output_filename, upload_dir)


def _is_processable_musescore_file(drive_file):
    is_musescore_file = (drive_file.mime_type == 'application/x-musescore') or \
                        (get_extension(drive_file.name) == '.mscx' and drive_file.mime_type == 'text/xml')
    if not is_musescore_file:
        return False

    # This will likely turn into a continue at some point if it doesn't get handled properly
    if len(drive_file.parents) != 1:
        raise ValueError(f'Musescore file id {drive_file.id} name {drive_file.name} does not have exactly 1 parent')

    return True


if __name__ == '__main__':
    main()
