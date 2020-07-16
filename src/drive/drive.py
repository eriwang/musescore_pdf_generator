import contextlib
import os
import tempfile

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from drive.google_auth import get_credentials

# What should this be able to do?
# - Get changes until up to date
# - Poll for changes, looking at the snapshot ID
# - Download a specific file that changed
# - Upload PDFs in the dir for that file
# - Be able to do a batch conversion on some directory
# - Hook up the change finding to the download/ gen/ upload pipeline (not the job of this class)
#
# - given a musescore file id:
#     - If it's in >1 parent, nope out. It's not clear where the PDF should be generated for that case.
#     - check if it's in the folder i want (which might need to be recursive file checks, annoyingly enough)'''
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

    @classmethod
    def create_authenticate_and_start(cls):
        return cls(build('drive', 'v3', credentials=get_credentials()))
