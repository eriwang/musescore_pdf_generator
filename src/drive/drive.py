import contextlib
from dataclasses import dataclass
import os
import tempfile

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from drive.google_auth import get_credentials


@dataclass
class DriveFile:
    id: str
    name: str
    mime_type: str
    parents: list

    def is_folder(self):
        return self.mime_type == 'application/vnd.google-apps.folder'

    @classmethod
    def create_from_drive_api_response(cls, response):
        return cls(id=response['id'],
                   name=response['name'],
                   mime_type=response['mimeType'],
                   parents=response['parents'])


class Drive:
    def __init__(self, service):
        self._service = service

    @contextlib.contextmanager
    def open_as_temporary_named_file(self, file_id, suffix=None):
        f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        downloader = MediaIoBaseDownload(f, self._service.files().get_media(fileId=file_id))

        download_complete = False
        while not download_complete:
            _, download_complete = downloader.next_chunk()

        f.close()
        yield f.name
        os.remove(f.name)

    def recursively_search_directory(self, directory_id):
        dir_drive_files = self._list_directory(directory_id)

        files = []
        dir_folders = []
        for drive_file in dir_drive_files:
            item_type_list = dir_folders if drive_file.is_folder() else files
            item_type_list.append(drive_file)

        for folder in dir_folders:
            files.extend(self.recursively_search_directory(folder.id))

        return files

    # Drive allows multiple files to have the same name, if one exists we just update it.
    def upload_or_update_file(self, filename, parent_directory_id):
        file_basename = os.path.basename(filename)
        matching_file_id = self._find_matching_file_in_dir(file_basename, parent_directory_id)

        file_metadata = {'name': file_basename}
        media_body = MediaFileUpload(filename)
        file_service = self._service.files()
        if matching_file_id is None:
            file_metadata['parents'] = [parent_directory_id]
            file_service.create(body=file_metadata, media_body=media_body).execute()
        else:
            # there's a newRevision boolean param as well, for now not set but maybe worth considering.
            file_service.update(fileId=matching_file_id, body=file_metadata, media_body=media_body).execute()

    @classmethod
    def create_authenticate_and_start(cls):
        return cls(build('drive', 'v3', credentials=get_credentials()))

    def _list_directory(self, directory_id):
        dir_items = self._service.files().list(
            q=f'parents in "{directory_id}" and trashed = false',
            fields='incompleteSearch, files/id, files/name, files/mimeType, files/parents'
        ).execute()
        if dir_items['incompleteSearch']:
            raise ValueError(f'Incomplete search for {directory_id}, not yet handled')

        return [DriveFile.create_from_drive_api_response(item) for item in dir_items['files']]

    def _find_matching_file_in_dir(self, file_basename, parent_directory_id):
        dir_drive_files = self._list_directory(parent_directory_id)
        matching_file_id = None
        for drive_file in dir_drive_files:
            if drive_file.is_folder() or drive_file.name != file_basename:
                continue
            if matching_file_id is not None:
                raise ValueError(f'Found multiple matches for {file_basename} in directory {parent_directory_id}')

            matching_file_id = drive_file.id

        return matching_file_id
