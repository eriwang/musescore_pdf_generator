import xml.etree.ElementTree as ET
import tempfile
import unittest

from musescore.score import Score
from utils.xml_utils import find_direct_children_with_tag_name

_SINGLE_PART_PATH = 'test_resources/single_part.mscz'
_MULTI_PART_SAME_NAME_PATH = 'test_resources/multi_part_same_name.mscz'
_MULTI_PART_MULTI_STAVES_PATH = 'test_resources/multi_part_multi_staves.mscz'
_MULTI_PART_ALREADY_ASSIGNED_PATH = 'test_resources/multi_part_already_assigned.mscz'


'''
What to test?
- Score metadata got copied over (say we check style and metaTag work_title)
- Part nodes are what I expect (what does that entail?)
    - names check out
    - staff count + id/ measure count (as a sanity check) checks out
- Staff nodes are what I expect
    - Only the IDs I expect
    - VBox? might need to add this in myself'''
class TestScore(unittest.TestCase):
    def test_split_write_single_part(self):
        _TITLE = 'Single Part'

        s = Score.create_from_file(_SINGLE_PART_PATH)
        parts = s.split_to_part_scores()
        self.assertEqual(len(parts), 1)

        root = _write_score_to_temp_file_and_read_xml(parts[0])
        score_node = self._find_exactly_one_direct_child(root, 'Score')
        self._assert_nonlinked_score_metadata_is_expected(score_node, _TITLE)

        part_node = self._find_exactly_one_direct_child(score_node, 'Part')
        self.assertEqual(self._find_exactly_one_direct_child(part_node, 'Staff').get('id'), '1')

        part_instrument_node = self._find_exactly_one_direct_child(part_node, 'Instrument')
        self.assertEqual(self._find_exactly_one_direct_child(part_instrument_node, 'longName').text, 'Piano')

        staff_node = self._find_exactly_one_direct_child(score_node, 'Staff')
        vbox_node = self._find_exactly_one_direct_child(staff_node, 'VBox')
        vbox_text_node = self._find_exactly_one_direct_child(vbox_node, 'Text')
        self.assertEqual(self._find_exactly_one_direct_child(vbox_text_node, 'style').text, 'Title')
        self.assertEqual(self._find_exactly_one_direct_child(vbox_text_node, 'text').text, _TITLE)

        self.assertEqual(len(find_direct_children_with_tag_name(staff_node, 'Measure')), 1)

    def test_split_write_multi_part_same_name(self):
        self.assertEqual(True, False)

    def test_split_write_multi_part_multi_staves(self):
        self.assertEqual(True, False)

    def test_split_multi_part_already_assigned_raises(self):
        self.assertEqual(True, False)

    def test_has_manual_parts(self):
        self.assertFalse(Score.create_from_file(_SINGLE_PART_PATH).has_manual_parts())
        self.assertFalse(Score.create_from_file(_MULTI_PART_SAME_NAME_PATH).has_manual_parts())
        self.assertFalse(Score.create_from_file(_MULTI_PART_MULTI_STAVES_PATH).has_manual_parts())
        self.assertTrue(Score.create_from_file(_MULTI_PART_ALREADY_ASSIGNED_PATH).has_manual_parts())

    def _assert_nonlinked_score_metadata_is_expected(self, score_xml, work_title):
        style_node = self._find_exactly_one_direct_child(score_xml, 'Style')
        spatium_node = self._find_exactly_one_direct_child(style_node, 'Spatium')
        self.assertEqual(spatium_node.text, '1.76389')  # true for all the resource files

        meta_tag_nodes = find_direct_children_with_tag_name(score_xml, 'metaTag')
        self.assertGreater(len(meta_tag_nodes), 1)

        # TODO: consider abstracting if reused
        work_title_nodes = [node for node in meta_tag_nodes if node.get('name') == 'workTitle']
        self.assertEqual(len(work_title_nodes), 1)
        self.assertEqual(work_title_nodes[0].text, work_title)

    def _find_exactly_one_direct_child(self, node, name):
        children = find_direct_children_with_tag_name(node, name)
        self.assertEqual(len(children), 1)
        return children[0]


def _write_score_to_temp_file_and_read_xml(score):
    with tempfile.TemporaryFile() as f:
        score.write_mscx_to_file(f)
        f.seek(0)
        return ET.fromstring(f.read())


if __name__ == '__main__':
    unittest.main()
