import random
import unittest
from unittest.mock import patch
from tools.ue3_textures import decode_dxt5, _decode_dxt5_reference, FormatError


class BC3AccelerationTests(unittest.TestCase):
    def test_ten_thousand_seeded_blocks_equal_python_oracle(self):
        data = random.Random(312313).randbytes(160000)
        self.assertEqual(decode_dxt5.__wrapped__(data, 400, 400),
                         _decode_dxt5_reference(data, 400, 400))

    def test_alpha_modes_equal_endpoints_and_all_selectors(self):
        blocks = []
        for a, b in [(0, 0), (0, 255), (255, 0), (255, 255), (1, 2), (254, 253), (1, 0)]:
            for selector in range(8):
                indices = sum(selector << (i * 3) for i in range(16))
                blocks.append(bytes([a, b]) + indices.to_bytes(6, 'little')
                              + bytes.fromhex('0000ffff') + bytes([0xe4]) * 4)
        data = b''.join(blocks)
        self.assertEqual(decode_dxt5.__wrapped__(data, len(blocks) * 4, 4),
                         _decode_dxt5_reference(data, len(blocks) * 4, 4))

    def test_rectangular_block_row_order_exact(self):
        for width, height in [(16, 64), (64, 16), (4, 128), (128, 4)]:
            data = random.Random(width).randbytes(width * height)
            self.assertEqual(decode_dxt5.__wrapped__(data, width, height),
                             _decode_dxt5_reference(data, width, height))

    def test_optional_decoder_absence_uses_dependency_free_oracle(self):
        data = random.Random(1).randbytes(16)
        with patch('tools.ue3_textures._decode_dxt5_pillow', return_value=None):
            self.assertEqual(decode_dxt5.__wrapped__(data, 4, 4),
                             _decode_dxt5_reference(data, 4, 4))

    def test_bad_buffers_fail_before_optional_codec(self):
        with patch('tools.ue3_textures._decode_dxt5_pillow') as codec:
            for data, width, height in [(b'', 4, 4), (bytes(16), 0, 4), (bytes(16), 3, 4)]:
                with self.assertRaises(FormatError):
                    decode_dxt5.__wrapped__(data, width, height)
            codec.assert_not_called()

    def test_mutable_input_keeps_reference_semantics(self):
        data = bytearray(random.Random(2).randbytes(16))
        with patch('tools.ue3_textures._decode_dxt5_pillow') as codec:
            for value in [0, 255]:
                data[0] = value
                self.assertEqual(decode_dxt5(data, 4, 4), _decode_dxt5_reference(data, 4, 4))
            codec.assert_not_called()


if __name__ == '__main__':
    unittest.main()
