import os
import tempfile
import time

from drive.drive import Drive
from musescore.pdf_conversion import convert_mscz_to_pdfs
from utils.os_path_utils import get_no_extension, get_extension


def run_drive_change_pdf_generator(drive_root_folder_id):
    d = Drive.create_authenticate_and_start()

    listening_file_ids = _refresh_listening_file_id_index_and_regen(d, drive_root_folder_id)
    counter = 1
    while True:
        if counter % 10 == 0:
            listening_file_ids = _refresh_listening_file_id_index_and_regen(d, drive_root_folder_id)

        for c in d.get_changes():
            if c.id not in listening_file_ids:
                continue
            if c.removed:
                listening_file_ids.remove(c.id)
                continue

            # You can save an API query by caching the results of the change and using it here, but this makes the code
            # (a tiny bit) easier to write.
            _generate_pdfs_for_file_id_if_needed(d, c.id)

        counter += 1
        time.sleep(5)


def _refresh_listening_file_id_index_and_regen(drive, root):
    listening_file_ids = {f.id for f in drive.recursively_search_directory(root)
                          if _is_processable_musescore_file(f)}
    for file_id in listening_file_ids:
        _generate_pdfs_for_file_id_if_needed(drive, file_id)

    return listening_file_ids


# TODO: this doesn't take into account if pdfs are missing but the mscz file hasn't changed
def _generate_pdfs_for_file_id_if_needed(drive, file_id):
    drive_file = drive.get_file_metadata(file_id)
    assert _is_processable_musescore_file(drive_file)

    gen_pdf_drive_files = [item for item in drive.list_directory(drive_file.parents[0])
                           if item.name.endswith('.gen.pdf')]
    if len(gen_pdf_drive_files) > 0 and \
            drive_file.modified_datetime < min([f.modified_datetime for f in gen_pdf_drive_files]):
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
    with tempfile.TemporaryDirectory as tempdir:
        convert_mscz_to_pdfs(musescore_file, tempdir, song_name)
        return [drive.upload_or_update_file(os.path.join(tempdir, gen_file), upload_dir)
                for gen_file in os.listdir(tempdir)]


def _is_processable_musescore_file(drive_file):
    is_musescore_file = (drive_file.mime_type == 'application/x-musescore') or \
                        (get_extension(drive_file.name) == '.mscx' and drive_file.mime_type == 'text/xml')
    if not is_musescore_file:
        return False

    # This will likely turn into a continue at some point if it doesn't get handled properly
    if len(drive_file.parents) != 1:
        raise ValueError(f'Musescore file id {drive_file.id} name {drive_file.name} does not have exactly 1 parent')

    return True
