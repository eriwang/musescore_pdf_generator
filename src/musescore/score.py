from collections import defaultdict
import copy
import xml.etree.ElementTree as ET
import zipfile

from utils.os_path_utils import get_extension
from utils.xml_utils import find_exactly_one, create_node_with_text


# I discovered shortly after implementing this that the MuseScore CLI can auto-generate parts when generating PDFs (but
# not mscz or mscx interestingly) if scores do not already have them. To do this, use the "-P" (--export-score-parts)
# flag with either -o (regular conversion) or -j (batch conversion, seems like you must specify a "score" pdf as well as
# the "parts" pdfs). However, I also want to manipulate the layout on the individual parts programatically, which is
# currently unsupported by the MuseScore batch conversion (can specify one style file for the whole job, not on a
# by-part basis). Therefore I'm still doing the manual splitting of MuseScore parts here when needed.
# TODO: fix <text><b></b><font face="ScoreText"></font>...<b><font face="FreeSerif"></font> = 188
#       </b></text>, new version is <text><sym>metNoteQuarterUp</sym> = 80</text>
class Score:
    def __init__(self, name, xml_tree):
        self.name = name
        self._xml_tree = xml_tree

    def get_number_of_parts(self):
        return len(self._xml_tree.findall('Score/Part'))

    def has_manual_parts(self):
        sub_score_nodes = self._xml_tree.findall('Score/Score')
        if len(sub_score_nodes) == 0:
            return False

        for sub_score_node in sub_score_nodes:
            if len(sub_score_node.findall('metaTag/[@name="partName"]')) != 1:
                raise ValueError('Found child score nodes, but no part name nodes')

        return True

    def generate_part_scores(self):
        if self.has_manual_parts():
            raise ValueError('Can\'t split part scores for score with manual parts')

        if len(self._xml_tree.findall('Score/Part')) == 1:
            return [Score(None, copy.deepcopy(self._xml_tree))]

        parts = _PartScore.create_parts_from_xml(self._xml_tree)
        self._fix_split_part_score_part_names(parts)

        return [Score(p.get_name(), p.xml_tree) for p in parts]

    def get_mscx_as_string(self):
        return ET.tostring(self._xml_tree)

    @classmethod
    def create_from_file(cls, filepath):
        ext = get_extension(filepath)
        if ext == '.mscx':
            return cls(None, ET.parse(filepath).getroot())
        if ext != '.mscz':
            raise ValueError(f'Unsupported filetype for file {filepath}')

        with zipfile.ZipFile(filepath) as mscz:
            path = zipfile.Path(mscz)
            for item in path.iterdir():
                if item.name.endswith('.mscx'):
                    return cls(None, ET.fromstring(item.read_text()))

        # TODO: fix tempo thing here

        raise ValueError(f'No .mscx files found in {filepath}')

    def _fix_split_part_score_part_names(self, part_scores):
        part_name_to_num_appearances = defaultdict(int)
        for part_node in self._xml_tree.findall('Score/Part'):
            part_name_to_num_appearances[find_exactly_one(part_node, 'Instrument/longName').text] += 1

        # Note that this does not handle if there's a "Violin 1", "Violin", and "Violin" part.
        # It's unclear what should be done (maybe the violin parts should be named "Solo Violin", for example)
        part_name_to_correct_part_number = defaultdict(int)
        for part in part_scores:
            part_name = part.get_name()
            is_duplicate_part_name = part_name_to_num_appearances[part_name] > 1
            if is_duplicate_part_name:
                part_name_to_correct_part_number[part_name] += 1
                part.set_name(f'{part_name} {part_name_to_correct_part_number[part_name]}')


class _PartScore:
    def __init__(self, xml_tree):
        self.xml_tree = xml_tree

    def get_name(self):
        return self._get_name_node().text

    # This only changes the VBox part name, as I don't believe the instrument longName does anything for one staff.
    def set_name(self, name):
        self._get_name_node().text = name

    # TODO: Losing some information during the split. Tempo, system text, rehearsal marks are what I've seen so far
    @classmethod
    def create_parts_from_xml(cls, xml_tree):
        vbox_node = find_exactly_one(xml_tree, 'Score/Staff/[@id="1"]/VBox')

        parts = []
        for part_index in range(len(xml_tree.findall('Score/Part'))):
            part_xml_tree = copy.deepcopy(xml_tree)

            # Ordering is important for these method calls, as they depend on each other's results.
            _PartScore._remove_unneeded_parts(part_xml_tree, part_index)
            _PartScore._remove_unneeded_staves_and_staff_vbox(part_xml_tree)
            # Layout breaks from the score are hopefully unneeded in the part itself, as the measure rendering has
            # different lines/ pages.
            _PartScore._remove_layout_breaks(part_xml_tree)
            _PartScore._add_vbox_with_part_text(part_xml_tree, vbox_node)
            _PartScore._fix_staff_ids(part_xml_tree)

            parts.append(cls(part_xml_tree))

        return parts

    def _get_name_node(self):
        vbox_text_nodes = self.xml_tree.findall('Score/Staff/[@id="1"]/VBox/Text')
        for vbox_text_node in vbox_text_nodes:
            if find_exactly_one(vbox_text_node, 'style').text == 'Instrument Name (Part)':
                return find_exactly_one(vbox_text_node, 'text')

        raise ValueError('No vbox part node found')

    @staticmethod
    def _remove_unneeded_parts(xml_tree, part_index):
        score_node = find_exactly_one(xml_tree, 'Score')
        for i, part_node in enumerate(score_node.findall('Part')):
            if i != part_index:
                score_node.remove(part_node)

    @staticmethod
    def _remove_unneeded_staves_and_staff_vbox(xml_tree):
        staff_ids = [staff.get('id') for staff in xml_tree.findall('Score/Part/Staff')]

        score_node = find_exactly_one(xml_tree, 'Score')
        for score_staff_node in score_node.findall('Staff'):
            if score_staff_node.get('id') not in staff_ids:
                score_node.remove(score_staff_node)
                continue

            existing_staff_vbox_node = score_staff_node.find('VBox')
            if existing_staff_vbox_node is not None:
                score_staff_node.remove(existing_staff_vbox_node)

    @staticmethod
    def _remove_layout_breaks(xml_tree):
        for measure_node in xml_tree.findall('Score/Staff/Measure'):
            layout_break_nodes = measure_node.findall('LayoutBreak')
            for n in layout_break_nodes:
                measure_node.remove(n)

    @staticmethod
    def _add_vbox_with_part_text(xml_tree, original_vbox_node):
        vbox_text_node = ET.Element('Text')
        vbox_text_node.extend([
            create_node_with_text('style', 'Instrument Name (Part)'),
            create_node_with_text('text', find_exactly_one(xml_tree, 'Score/Part/Instrument/longName').text)
        ])

        vbox_node = copy.deepcopy(original_vbox_node)
        vbox_node.append(vbox_text_node)

        xml_tree.find('Score/Staff').insert(0, vbox_node)

    @staticmethod
    def _fix_staff_ids(xml_tree):
        staff_nodes = xml_tree.findall('Score/Staff')
        part_staff_nodes = xml_tree.findall('Score/Part/Staff')
        assert len(staff_nodes) == len(part_staff_nodes)

        for i, (staff_node, part_staff_node) in enumerate(zip(staff_nodes, part_staff_nodes)):
            staff_id = str(i + 1)
            staff_node.set('id', staff_id)
            part_staff_node.set('id', staff_id)
