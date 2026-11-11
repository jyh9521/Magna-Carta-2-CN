"""Synthetic native records only; no original game assets in test fixtures."""
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ue3_native_coverage import (
    FormatError, digest, inspect_package, main, parse_shader_cache_payload, parse_static_mesh_payload,
)


NAMES = ["None", "FScreenVertexShader", "FScreenPixelShader", "FLocalVertexFactory"]
SERIAL_OFFSET = 4096


def integers(*values):
    return struct.pack(">" + "I" * len(values), *values)


def mesh_fixture():
    data = bytearray(integers(0, 0, 0))  # NetIndex + None FName.
    data += struct.pack(">7f", 0, 0, 0, 1, 1, 1, 2)
    data += integers(0, 0, 0, 15, 1)  # BodySetup, empty KDOP arrays, version, LODs.
    data += integers(0, 0, 0, SERIAL_OFFSET + len(data) + 16)
    data += integers(1) + integers(0, 1, 1, 0, 1, 0, 0)  # One section.
    data += integers(1, 40, 1, 1)  # UV sets, stride, vertex count, array count.
    data += struct.pack(">3f", 1, 2, 3) + bytes(20) + struct.pack(">2f", 0.5, 0.5)
    data += integers(1, 3) + struct.pack(">3H", 0, 0, 0)
    data += integers(0, 0, 0)  # Wireframe, edges, face flags.
    data += integers(1, 0, 0, 0, 0)
    return bytes(data)


def shader_fixture(parameter_pairs=()):
    data = bytearray(integers(0, 0, 0))
    data += b"\x02" + integers(1, 1, 0, 0x12345678)  # Platform + CRC map.
    data += integers(0, 1)  # Empty vertex factory map, one shader.
    data += integers(1, 0) + bytes(range(16))
    end_field = len(data)
    data += bytes(4) + b"\x02\x00"
    code = integers(0x102a1101, 48, 12, *([0] * 9)) + bytes(12)
    data += integers(len(code)) + code
    data += bytes(range(16)) + integers(1, 0, 1)
    for base, count in parameter_pairs:
        data += struct.pack(">HH", base, count)
    struct.pack_into(">I", data, end_field, SERIAL_OFFSET + len(data))
    data += integers(0, 1)  # Material maps absent; one global reference.
    data += integers(1, 0) + bytes(range(16)) + integers(1, 0)
    return bytes(data)


class NativeCoverageTests(unittest.TestCase):
    def mesh(self, data=None):
        return parse_static_mesh_payload(mesh_fixture() if data is None else data,
                                         NAMES, SERIAL_OFFSET, 0, 1)

    def shader(self, data=None):
        return parse_shader_cache_payload(shader_fixture() if data is None else data,
                                          NAMES, SERIAL_OFFSET)

    @staticmethod
    def change_u32(data, report, field_name, value):
        data = bytearray(data)
        field = next(field for field in report["fields"] if field["name"] == field_name)
        struct.pack_into(">I", data, field["relative_range"][0], value)
        return bytes(data)

    def test_mesh_complete_contiguous_coverage(self):
        report = self.mesh()
        self.assertTrue(report["fully_consumed"])
        self.assertEqual(report["native_string_fields"], 0)
        self.assertEqual(report["tagged_strings"], [])
        self.assertEqual(report["lods"][0]["num_vertices"], 1)
        self.assertEqual(report["fields"][-1]["relative_range"][1], len(mesh_fixture()))

    def test_mesh_unknown_version_rejected(self):
        data = self.change_u32(mesh_fixture(), self.mesh(), "InternalVersion", 17)
        with self.assertRaisesRegex(FormatError, "InternalVersion"):
            self.mesh(data)

    def test_mesh_bulk_offset_rejected(self):
        data = self.change_u32(mesh_fixture(), self.mesh(), "LODs[0].RawTriangles.offset", 1)
        with self.assertRaisesRegex(FormatError, "triangle bulk"):
            self.mesh(data)

    def test_mesh_unknown_stride_rejected(self):
        data = self.change_u32(mesh_fixture(), self.mesh(), "LODs[0].VertexStride", 32)
        with self.assertRaisesRegex(FormatError, "stride"):
            self.mesh(data)

    def test_mesh_count_mismatch_rejected(self):
        data = self.change_u32(mesh_fixture(), self.mesh(), "LODs[0].NumVerticesDuplicate", 2)
        with self.assertRaisesRegex(FormatError, "count mismatch"):
            self.mesh(data)

    def test_mesh_index_outside_vertices_rejected(self):
        data = bytearray(mesh_fixture())
        field = next(f for f in self.mesh()["fields"] if f["name"] == "LODs[0].Indices")
        struct.pack_into(">H", data, field["relative_range"][0], 1)
        with self.assertRaisesRegex(FormatError, "index outside"):
            self.mesh(bytes(data))

    def test_mesh_nonfinite_vertex_rejected(self):
        data = bytearray(mesh_fixture())
        field = next(f for f in self.mesh()["fields"] if f["name"] == "LODs[0].VertexUV")
        struct.pack_into(">f", data, field["relative_range"][0], float("nan"))
        with self.assertRaisesRegex(FormatError, "non-finite"):
            self.mesh(bytes(data))

    def test_mesh_truncated_and_extra_bytes_rejected(self):
        for data in (mesh_fixture()[:-1], mesh_fixture() + b"\x00"):
            with self.subTest(size=len(data)), self.assertRaises(FormatError):
                self.mesh(data)

    def test_mesh_unrecognized_footer_rejected(self):
        data = bytearray(mesh_fixture())
        data[-1] = 1
        with self.assertRaisesRegex(FormatError, "footer profile"):
            self.mesh(bytes(data))

    def test_shader_complete_crosslinked_coverage(self):
        report = self.shader()
        self.assertTrue(report["fully_consumed"])
        self.assertEqual(report["known_native_string_fields"], 0)
        self.assertIsNone(report["native_string_fields"])
        self.assertEqual(report["material_shader_maps_count"], 0)
        self.assertEqual(report["global_shader_map"][0]["shader_index"], 0)

    def test_shader_nonempty_material_maps_not_silently_skipped(self):
        data = self.change_u32(shader_fixture(), self.shader(), "MaterialShaderMaps.count", 1)
        with self.assertRaisesRegex(FormatError, "native FString parser"):
            self.shader(data)

    def test_shader_parameter_bytes_not_promoted_to_verified_semantics(self):
        report = self.shader(shader_fixture([(4, 1)]))
        self.assertTrue(report["fully_consumed"])
        self.assertFalse(report["native_semantic_coverage_complete"])
        self.assertIsNone(report["native_string_fields"])
        self.assertEqual(report["semantic_unresolved_bytes"], 4)
        self.assertEqual(report["semantic_unresolved_regions"][0]["semantic_grade"],
                         "High-confidence deduction")

    def test_shader_parameter_layout_outside_profile_rejected(self):
        with self.assertRaisesRegex(FormatError, "parameter register pair"):
            self.shader(shader_fixture([(4, 33)]))

    def test_shader_duplicate_guid_rejected(self):
        data = bytearray(shader_fixture())
        field = next(f for f in self.shader()["fields"] if f["name"] == "Shaders[0].GUIDDuplicate")
        data[field["relative_range"][0]] ^= 1
        with self.assertRaisesRegex(FormatError, "GUID mismatch"):
            self.shader(bytes(data))

    def test_shader_compiled_size_rejected(self):
        data = bytearray(shader_fixture())
        field = next(f for f in self.shader()["fields"] if f["name"] == "Shaders[0].Bytecode")
        struct.pack_into(">I", data, field["relative_range"][0] + 8, 16)
        with self.assertRaisesRegex(FormatError, "header/body size"):
            self.shader(bytes(data))

    def test_shader_signature_frequency_rejected(self):
        data = bytearray(shader_fixture())
        field = next(f for f in self.shader()["fields"] if f["name"] == "Shaders[0].Target")
        data[field["relative_range"][0] + 1] = 1
        with self.assertRaisesRegex(FormatError, "signature/frequency"):
            self.shader(bytes(data))

    def test_shader_invalid_reference_rejected(self):
        data = bytearray(shader_fixture())
        field = next(f for f in self.shader()["fields"] if f["name"] == "GlobalShaderMap[0].GUID")
        data[field["relative_range"][0]] ^= 1
        with self.assertRaisesRegex(FormatError, "resolve uniquely"):
            self.shader(bytes(data))

    def test_shader_empty_global_map_rejected(self):
        data = self.change_u32(shader_fixture(), self.shader(), "GlobalShaderMap.count", 0)
        with self.assertRaisesRegex(FormatError, "bijectively"):
            self.shader(data)

    def test_shader_truncated_and_extra_bytes_rejected(self):
        for data in (shader_fixture()[:-1], shader_fixture() + b"\x00"):
            with self.subTest(size=len(data)), self.assertRaises(FormatError):
                self.shader(data)

    def test_package_source_lock_precedes_decode(self):
        with self.assertRaisesRegex(FormatError, "SHA-256 mismatch"):
            inspect_package(b"not-a-package", "0" * 64, ["Engine.StaticMesh"])

    def test_cli_same_source_output_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "package.bin"
            raw = b"original source bytes"
            source.write_bytes(raw)
            argv = ["native-coverage", str(source), "--sha256", digest(raw),
                    "--class", "Engine.StaticMesh", "--output", str(source)]
            with patch("sys.argv", argv), self.assertRaisesRegex(FormatError, "new file"):
                main()
            self.assertEqual(source.read_bytes(), raw)

    def test_cli_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "package.bin"
            output = Path(directory) / "report.json"
            source.write_bytes(b"source")
            output.write_bytes(b"existing report")
            argv = ["native-coverage", str(source), "--sha256", digest(b"source"),
                    "--class", "Engine.StaticMesh", "--output", str(output)]
            with patch("sys.argv", argv), self.assertRaisesRegex(FormatError, "new file"):
                main()
            self.assertEqual(source.read_bytes(), b"source")
            self.assertEqual(output.read_bytes(), b"existing report")

    def test_cli_source_hash_checked_before_loading_dll(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "package.bin"
            source.write_bytes(b"source")
            argv = ["native-coverage", str(source), "--sha256", "0" * 64,
                    "--class", "Engine.StaticMesh", "--lzx", str(Path(directory) / "never.dll"),
                    "--lzx-sha256", "0" * 64, "--output", str(Path(directory) / "new-report.json")]
            with patch("sys.argv", argv), patch("tools.ue3_native_coverage.LzxDecoder") as decoder:
                with self.assertRaisesRegex(FormatError, "source package SHA-256"):
                    main()
                decoder.assert_not_called()

    def test_cli_dll_hash_checked_before_loading_dll(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "package.bin"
            library = Path(directory) / "decoder.dll"
            source.write_bytes(b"source")
            library.write_bytes(b"unverified DLL bytes")
            argv = ["native-coverage", str(source), "--sha256", digest(b"source"),
                    "--class", "Engine.StaticMesh", "--lzx", str(library),
                    "--lzx-sha256", "0" * 64, "--output", str(Path(directory) / "new-report.json")]
            summary = dict(version=446, licensee_version=25, byte_order="big")
            with patch("sys.argv", argv), patch("tools.ue3_native_coverage.parse_summary", return_value=summary), \
                    patch("tools.ue3_native_coverage.LzxDecoder") as decoder:
                with self.assertRaisesRegex(FormatError, "LZX DLL SHA-256"):
                    main()
                decoder.assert_not_called()


if __name__ == "__main__":
    unittest.main()
