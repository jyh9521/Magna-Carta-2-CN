import unittest
from tools.pure_bytes_cache import bounded_bytes_cache


class PureBytesCacheTests(unittest.TestCase):
    def test_exact_bytes_and_dimensions_are_part_of_key(self):
        calls = []
        @bounded_bytes_cache(100)
        def f(data, width, height):
            calls.append(1)
            return data + bytes([width, height])
        self.assertEqual(f(b'a', 2, 3), f(bytes([97]), 2, 3))
        self.assertEqual(len(calls), 1)
        self.assertNotEqual(f(b'b', 2, 3), f(b'a', 3, 2))
        self.assertEqual(len(calls), 3)

    def test_input_and_output_budget_and_lru_eviction(self):
        calls = []
        @bounded_bytes_cache(8)
        def f(data):
            calls.append(data)
            return data
        for data in [b'aa', b'bb', b'aa', b'cc', b'bb']:
            self.assertEqual(f(data), data)
        self.assertEqual(calls, [b'aa', b'bb', b'cc', b'bb'])

    def test_oversized_results_are_not_retained(self):
        calls = []
        @bounded_bytes_cache(3)
        def f(data):
            calls.append(1)
            return data * 4
        self.assertEqual(f(b'a'), f(b'a'))
        self.assertEqual(len(calls), 2)
        calls.clear()
        @bounded_bytes_cache(100, max_entries=2)
        def empty(data, index):
            calls.append(index)
            return b''
        for index in [1, 2, 3, 1]:
            self.assertEqual(empty(b'', index), b'')
        self.assertEqual(calls, [1, 2, 3, 1])

    def test_mutable_inputs_and_exceptions_are_not_cached(self):
        @bounded_bytes_cache(100)
        def f(data):
            if not data:
                raise ValueError('empty')
            return bytes(data)
        data = bytearray(b'a')
        self.assertEqual(f(data), b'a')
        data[0] = 98
        self.assertEqual(f(data), b'b')
        for _ in range(2):
            with self.assertRaises(ValueError):
                f(b'')

    def test_keyword_order_does_not_change_result(self):
        calls = []
        @bounded_bytes_cache(100)
        def f(data, width, height):
            calls.append(1)
            return data * width * height
        self.assertEqual(f(b'a', height=3, width=2), f(b'a', width=2, height=3))
        self.assertEqual(len(calls), 1)

    def test_decoder_cached_and_uncached_bytes_identical(self):
        from tools.ue3_textures import decode_dxt5
        block = bytes([255, 0]) + bytes(6) + bytes.fromhex('ffff0000') + bytes(4)
        self.assertEqual(decode_dxt5(block, 4, 4), decode_dxt5.__wrapped__(block, 4, 4))
        self.assertEqual(decode_dxt5(block, 4, 4), decode_dxt5(block, 4, 4))


if __name__ == '__main__':
    unittest.main()
