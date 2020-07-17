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
        dir_items = self._service.files().list(
            q=f'parents in "{directory_id}" and trashed = false',
            fields='incompleteSearch, files/id, files/name, files/mimeType, files/parents'
        ).execute()
        if dir_items['incompleteSearch']:
            raise ValueError(f'Incomplete search for {directory_id}, not yet handled')

        dir_drive_files = [DriveFile.create_from_drive_api_response(item) for item in dir_items['files']]

        files = []
        dir_folders = []
        for drive_file in dir_drive_files:
            item_type_list = dir_folders if drive_file.is_folder() else files
            item_type_list.append(drive_file)

        for folder in dir_folders:
            files.extend(self.recursively_search_directory(folder.id))

        # TODO: want name, mimeType, id, parents (for now hard fail if mscz has multiple parents)
        return files

    def upload_file(self, filename, parent_directory_id):
        file_metadata = {
            'name': os.path.basename(filename),
            'parents': [parent_directory_id]
        }
        self._service.files().create(body=file_metadata, media_body=MediaFileUpload(filename)).execute()

    @classmethod
    def create_authenticate_and_start(cls):
        return cls(build('drive', 'v3', credentials=get_credentials()))
