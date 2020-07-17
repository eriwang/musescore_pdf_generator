import contextlib
from dataclasses import dataclass
import datetime
import os
import tempfile

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from drive.google_auth import get_credentials


class Drive:
    def __init__(self, service):
        self._service = service
        self._changes_page_token = None

    def get_file_metadata(self, file_id):
        response = self._service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, parents, modifiedTime'
        ).execute()
        return DriveFile.create_from_drive_api_response(response)

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
        dir_drive_files = self.list_directory(directory_id)

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
        file_id = self._find_matching_file_in_dir(file_basename, parent_directory_id)

        file_metadata = {'name': file_basename}
        media_body = MediaFileUpload(filename)
        file_service = self._service.files()
        if file_id is None:
            file_metadata['parents'] = [parent_directory_id]
            file_id = file_service.create(body=file_metadata, media_body=media_body).execute()['id']
        else:
            # there's a newRevision boolean param as well, for now not set but maybe worth considering.
            file_service.update(fileId=file_id, body=file_metadata, media_body=media_body).execute()

        return file_id

    def list_directory(self, directory_id):
        dir_items = self._service.files().list(
            q=f'parents in "{directory_id}" and trashed = false',
            fields='incompleteSearch, files/id, files/name, files/mimeType, files/parents, files/modifiedTime'
        ).execute()
        if dir_items['incompleteSearch']:
            raise ValueError(f'Incomplete search for {directory_id}, not yet handled')

        return [DriveFile.create_from_drive_api_response(item) for item in dir_items['files']]

    def get_changes(self):
        if self._changes_page_token is None:
            self._changes_page_token = self._service.changes().getStartPageToken().execute()['startPageToken']

        changes = []
        found_new_start_page_token = False
        while not found_new_start_page_token:
            response = self._service.changes().list(
                pageToken=self._changes_page_token,
                fields='newStartPageToken, nextPageToken, changes/removed, changes/file/id',
                spaces='drive'
            ).execute()

            print(f'queried changes with token {self._changes_page_token}, {len(response["changes"])} results')
            for change in response['changes']:
                changes.append(DriveChange.create_list_from_drive_api_response(change))

            if 'newStartPageToken' in response:
                found_new_start_page_token = True
                self._changes_page_token = response['newStartPageToken']
            else:
                self._changes_page_token = response['nextPageToken']

        return changes

    def move_file_to_trash(self, file_id):
        self._service.files().update(fileId=file_id, body={'trashed': True}).execute()

    @classmethod
    def create_authenticate_and_start(cls):
        return cls(build('drive', 'v3', credentials=get_credentials()))

    def _find_matching_file_in_dir(self, file_basename, parent_directory_id):
        dir_drive_files = self.list_directory(parent_directory_id)
        matching_file_id = None
        for drive_file in dir_drive_files:
            if drive_file.is_folder() or drive_file.name != file_basename:
                continue
            if matching_file_id is not None:
                raise ValueError(f'Found multiple matches for {file_basename} in directory {parent_directory_id}')

            matching_file_id = drive_file.id

        return matching_file_id


@dataclass
class DriveFile:
    id: str
    name: str
    mime_type: str
    parents: list
    modified_datetime: datetime.datetime

    def is_folder(self):
        return self.mime_type == 'application/vnd.google-apps.folder'

    @classmethod
    def create_from_drive_api_response(cls, response):
        # modifiedTime is given in RFC3339 format. This app doesn't care about time zone (yet) so just converting to
        # python datetimes directly without worrying about time zone.
        modified_datetime = datetime.datetime.strptime(response['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return cls(id=response['id'],
                   name=response['name'],
                   mime_type=response['mimeType'],
                   parents=response['parents'],
                   modified_datetime=modified_datetime)


@dataclass
class DriveChange:
    id: str
    removed: bool

    @classmethod
    def create_list_from_drive_api_response(cls, response):
        return cls(id=response['file']['id'],
                   removed=response['removed'])
