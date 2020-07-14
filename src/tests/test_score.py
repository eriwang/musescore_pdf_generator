import xml.etree.ElementTree as ET
import tempfile
import unittest

from musescore.score import Score

_SINGLE_PART_PATH = 'test_resources/single_part.mscz'
_MULTI_PART_SAME_NAME_PATH = 'test_resources/multi_part_same_name.mscz'
_MULTI_PART_MULTI_STAVES_PATH = 'test_resources/multi_part_multi_staves.mscz'
_MULTI_PART_MANUAL_PARTS_PATH = 'test_resources/multi_part_manual_parts.mscz'


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
    def setUp(self):
        self._single_part_score = Score.create_from_file(_SINGLE_PART_PATH)
        self._multi_part_same_name_score = Score.create_from_file(_MULTI_PART_SAME_NAME_PATH)
        self._multi_part_multi_staves_score = Score.create_from_file(_MULTI_PART_MULTI_STAVES_PATH)
        self._multi_part_manual_parts_score = Score.create_from_file(_MULTI_PART_MANUAL_PARTS_PATH)

    def test_split_write_single_part(self):
        _TITLE = 'Single Part'

        parts = self._single_part_score.split_to_part_scores()
        self.assertEqual(len(parts), 1)

        root = _write_score_to_temp_file_and_read_xml(parts[0])
        score_node = self._find_exactly_one(root, 'Score')
        self._assert_nonlinked_score_metadata_is_expected(score_node, _TITLE)

        part_node = self._find_exactly_one(score_node, 'Part')
        self.assertEqual(self._find_exactly_one(part_node, 'Staff').get('id'), '1')
        self.assertEqual(self._find_exactly_one(part_node, 'Instrument/longName').text, 'Piano')

        staff_node = self._find_exactly_one(score_node, 'Staff')
        vbox_text_node = self._find_exactly_one(staff_node, 'VBox/Text')
        self.assertEqual(self._find_exactly_one(vbox_text_node, 'style').text, 'Title')
        self.assertEqual(self._find_exactly_one(vbox_text_node, 'text').text, _TITLE)

        self.assertEqual(len(staff_node.findall('Measure')), 1)

    def test_split_write_multi_part_same_name(self):
        self.assertEqual(True, False)

    def test_split_write_multi_part_multi_staves(self):
        self.assertEqual(True, False)

    def test_split_multi_part_already_assigned_raises(self):
        with self.assertRaises(ValueError):
            self._multi_part_manual_parts_score.split_to_part_scores()

    def test_has_manual_parts(self):
        self.assertFalse(self._single_part_score.has_manual_parts())
        self.assertFalse(self._multi_part_same_name_score.has_manual_parts())
        self.assertFalse(self._multi_part_multi_staves_score.has_manual_parts())
        self.assertTrue(self._multi_part_manual_parts_score.has_manual_parts())

    def _assert_nonlinked_score_metadata_is_expected(self, score_xml, work_title):
        # MuseScore default, true for all the resource files
        self.assertEqual(self._find_exactly_one(score_xml, 'Style/Spatium').text, '1.76389')
        self.assertGreater(len(score_xml.findall('metaTag')), 1)
        self.assertEqual(self._find_exactly_one(score_xml, 'metaTag/[@name="workTitle"]').text, work_title)

    def _find_exactly_one(self, node, findall_arg):
        children = node.findall(findall_arg)
        self.assertEqual(len(children), 1)
        return children[0]


def _write_score_to_temp_file_and_read_xml(score):
    with tempfile.TemporaryFile() as f:
        score.write_mscx_to_file(f)
        f.seek(0)
        return ET.fromstring(f.read())


if __name__ == '__main__':
    unittest.main()
