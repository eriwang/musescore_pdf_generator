from collections import defaultdict, namedtuple
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

_Part = namedtuple('_Part', ['index', 'name', 'staff_ids', 'xml'])


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

        part_nodes = list(self._xml_tree.findall('Score/Part'))
        if len(part_nodes) == 1:
            return [Score(copy.deepcopy(self._xml_tree))]

        parts = []
        part_name_to_num_appearances = defaultdict(int)
        for index, part in enumerate(self._xml_tree.findall('Score/Part')):
            name_nodes = part.findall('Instrument/longName')
            assert len(name_nodes) == 1

            name = name_nodes[0].text
            part_name_to_num_appearances[name] += 1

            parts.append(_Part(
                index=index,
                name=name,
                staff_ids=[staff.get('id') for staff in part.findall('Staff')],
                xml=copy.deepcopy(self._xml_tree)
            ))

        # Note that this does not handle if there's a "Violin 1", "Violin", and "Violin" part,
        # as it's unclear what should be done (maybe the violin parts should be named "Solo Violin", for example)
        part_name_to_current_number = defaultdict(int)
        for part in parts:
            is_duplicate_part = part_name_to_num_appearances[part.name] > 1
            if is_duplicate_part:
                part_name_to_current_number[part.name] += 1
                part._replace(name=f'{part.name} {part_name_to_current_number[part.name]}')

            score_nodes = part.xml.findall('Score')
            assert len(score_nodes) == 1
            score_node = score_nodes[0]

            for index, part_node in enumerate(score_node.findall('Part')):
                if index != part.index:
                    score_node.remove(part_node)

            for staff in score_node.findall('Staff'):
                if staff.get('id') not in part.staff_ids:
                    score_node.remove(staff)

        # notes:
        # - should have VBox (copy from original to keep subtitle and whatnot?)
        # - staff id needs to start at 1

        return [Score(p.xml) for p in parts]

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
