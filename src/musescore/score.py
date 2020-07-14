import copy
import os
import xml.etree.ElementTree as ET
import zipfile

# App flow:
# - Get an mscz or mscx
# - Read the XML
# - If it has parts already
#   - All good
# - If not:
#   - Split the XML into the associated parts
#       - Get parts
#           - Save Part.trackName, if there's dupes fix them based on ordering.
#           - Save Part.staff[id]
#       - Make new XML for each part
#           - Delete staves that don't match the staff id
#           - Make the staff.vbox element
#           - Save XML to mscx
# - Toss files into musescore for the conversion to pdf
#   - If it's a custom part mscx:
#       - Try the minimum layout settings, convert, and check PDF page count (that's the minimum page count)
#       - Increase the layout settings (TBD what I change), convert, and check PDF page count again.
#           - If PDF page count > min PDF page count, then final PDF is the previous one.
#   - If not, just convert with the parts and you're done

class Score:
    def __init__(self, xml_tree):
        self._xml_tree = xml_tree

    def has_manual_parts(self):
        sub_score_nodes = self._xml_tree.findall('Score/Score')
        if len(sub_score_nodes) == 0:
            return False

        for sub_score_node in sub_score_nodes:
            if len(sub_score_node.findall('metaTag/[@name="partName"]')) != 1:
                raise ValueError('Found child score nodes, but no part name nodes')

        return True

    def split_to_part_scores(self):
        if self.has_manual_parts():
            raise ValueError('Not splitting part scores for score with manual parts')

        return [Score(copy.deepcopy(self._xml_tree))]

    def write_mscx_to_file(self, f):
        ET.ElementTree(self._xml_tree).write(f, encoding='UTF-8')

    @classmethod
    def create_from_file(cls, filepath):
        _, ext = os.path.splitext(filepath)

        if ext == '.mscx':
            return cls(ET.parse(filepath))
        if ext != '.mscz':
            raise ValueError(f'Unsupported filetype for file {filepath}')

        with zipfile.ZipFile(filepath) as mscz:
            path = zipfile.Path(mscz)
            for item in path.iterdir():
                if item.name.endswith('.mscx'):
                    return cls(ET.fromstring(item.read_text()))

        raise ValueError(f'No .mscx files found in {filepath}')
