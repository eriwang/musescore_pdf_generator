import xml.etree.ElementTree as ET
import unittest

from musescore.score import Score
from utils.xml_utils import find_exactly_one

_SINGLE_PART_PATH = 'test_resources/single_part.mscz'
_MULTI_PART_SAME_NAME_PATH = 'test_resources/multi_part_same_name.mscz'
_MULTI_PART_MULTI_STAVES_PATH = 'test_resources/multi_part_multi_staves.mscz'
_MULTI_PART_MANUAL_PARTS_PATH = 'test_resources/multi_part_manual_parts.mscz'


class TestScore(unittest.TestCase):
    def setUp(self):
        self._single_part_score = Score.create_from_file(_SINGLE_PART_PATH)
        self._multi_part_same_name_score = Score.create_from_file(_MULTI_PART_SAME_NAME_PATH)
        self._multi_part_multi_staves_score = Score.create_from_file(_MULTI_PART_MULTI_STAVES_PATH)
        self._multi_part_manual_parts_score = Score.create_from_file(_MULTI_PART_MANUAL_PARTS_PATH)

    def test_split_write_single_part(self):
        _TITLE = 'Single Part'

        [part] = self._single_part_score.generate_part_scores()

        root = _write_score_to_string_and_read_xml(part)
        self._assert_nonlinked_score_metadata_correct(root, _TITLE)
        self._assert_part_correct(root, ['1'], 'Piano')
        self._assert_staves_one_measure(root)
        self._assert_vbox_field_match(root, 'Title', _TITLE)

    def test_split_write_multi_part_same_name(self):
        _TITLE = 'Multi Part'

        [violin1, violin2] = self._multi_part_same_name_score.generate_part_scores()

        violin1_root = _write_score_to_string_and_read_xml(violin1)
        self._assert_nonlinked_score_metadata_correct(violin1_root, _TITLE)
        self._assert_part_correct(violin1_root, ['1'], 'Violin')
        self._assert_staves_one_measure(violin1_root)
        self._assert_vbox_field_match(violin1_root, 'Title', _TITLE)
        self._assert_vbox_field_match(violin1_root, 'Instrument Name (Part)', 'Violin 1')

        violin2_root = _write_score_to_string_and_read_xml(violin2)
        self._assert_nonlinked_score_metadata_correct(violin2_root, _TITLE)
        self._assert_part_correct(violin2_root, ['1'], 'Violin')
        self._assert_staves_one_measure(violin2_root)
        self._assert_vbox_field_match(violin2_root, 'Title', _TITLE)
        self._assert_vbox_field_match(violin2_root, 'Instrument Name (Part)', 'Violin 2')

    def test_split_write_multi_part_multi_staves(self):
        _TITLE = 'Multi Part with Multi Staves'

        [violin, piano] = self._multi_part_multi_staves_score.generate_part_scores()

        violin_root = _write_score_to_string_and_read_xml(violin)
        self._assert_nonlinked_score_metadata_correct(violin_root, _TITLE)
        self._assert_part_correct(violin_root, ['1'], 'Violin')
        self._assert_staves_one_measure(violin_root)
        self._assert_vbox_field_match(violin_root, 'Title', _TITLE)
        self._assert_vbox_field_match(violin_root, 'Instrument Name (Part)', 'Violin')

        piano_root = _write_score_to_string_and_read_xml(piano)
        self._assert_nonlinked_score_metadata_correct(piano_root, _TITLE)
        self._assert_part_correct(piano_root, ['1', '2'], 'Piano')
        self._assert_staves_one_measure(piano_root)
        self._assert_vbox_field_match(piano_root, 'Title', _TITLE)
        self._assert_vbox_field_match(piano_root, 'Instrument Name (Part)', 'Piano')

    def test_split_multi_part_already_assigned_raises(self):
        with self.assertRaises(ValueError):
            self._multi_part_manual_parts_score.generate_part_scores()

    def test_has_manual_parts(self):
        self.assertFalse(self._single_part_score.has_manual_parts())
        self.assertFalse(self._multi_part_same_name_score.has_manual_parts())
        self.assertFalse(self._multi_part_multi_staves_score.has_manual_parts())
        self.assertTrue(self._multi_part_manual_parts_score.has_manual_parts())

    # Assertion Helpers
    def _assert_nonlinked_score_metadata_correct(self, root, work_title):
        score_xml = find_exactly_one(root, 'Score')

        # MuseScore default, true for all the resource files
        self.assertEqual(find_exactly_one(score_xml, 'Style/Spatium').text, '1.76389')
        self.assertGreater(len(score_xml.findall('metaTag')), 1)
        self.assertEqual(find_exactly_one(score_xml, 'metaTag/[@name="workTitle"]').text, work_title)

    def _assert_part_correct(self, root, staff_ids, instrument_long_name):
        part_node = find_exactly_one(root, 'Score/Part')
        self.assertListEqual([s.get('id') for s in part_node.findall('Staff')], staff_ids)
        self.assertEqual(find_exactly_one(part_node, 'Instrument/longName').text, instrument_long_name)

    def _assert_staves_one_measure(self, root):
        for staff_node in root.findall('Score/Staff'):
            self.assertEqual(len(staff_node.findall('Measure')), 1)

    def _assert_vbox_field_match(self, root, field_name, field_value):
        vbox_node = find_exactly_one(root, 'Score/Staff/VBox')
        matching_nodes = 0
        for vbox_text_node in vbox_node.findall('Text'):
            if find_exactly_one(vbox_text_node, 'style').text == field_name:
                self.assertEqual(find_exactly_one(vbox_text_node, 'text').text, field_value)
                matching_nodes += 1

        self.assertEqual(matching_nodes, 1, 'Did not find a matching node')


def _write_score_to_string_and_read_xml(score):
    return ET.fromstring(score.get_mscx_as_string())


if __name__ == '__main__':
    unittest.main()
