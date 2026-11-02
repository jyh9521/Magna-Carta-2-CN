import copy
import json
import struct
from pathlib import Path
import tempfile
import unittest

from tools import texture_dark_bands as bands
from tools import repair_texture_dark_bands as builder
from tools.reface_font import sha
from tools.replace_texture_regions import selected, replace_tiles
from tools.texture_layout import decode_texture, rect_units
from tools.texture_overlay import render_label, rgba_crop
from tools.repair_texture_labels import revise
import test_repair_texture_labels as fixtures
from test_supplement_font import stored_decoder


class DarkBandTests(unittest.TestCase):
    def fixture(self, root):
        recipe, data, obj, label = fixtures.LabelRepairTests().fixture(root)
        return data, obj, label, Path(root, 'font.ttf').read_bytes()

    def test_real_raster_band_rgb_improves_without_changing_any_alpha(self):
        with tempfile.TemporaryDirectory() as root:
            data, obj, label, font = self.fixture(root)
            tx = selected(data, obj, stored_decoder)[3]
            tiles, proof = bands.repair(tx, label, font, [56])
            self.assertGreater(proof['changed_blocks'], 0)
            self.assertEqual(tx['tiles'], selected(data, obj, stored_decoder)[3]['tiles'])
            self.assertEqual(decode_texture(tx)[3::4], decode_texture(tx, tiles)[3::4])
            for i in range(0, len(tiles), 16):
                self.assertEqual(tiles[i:i+8], tx['tiles'][i:i+8])
            allowed = set(rect_units(tx['layout'], label['rect']))
            for i in range(0, len(tiles), 16):
                if i not in allowed:
                    self.assertEqual(tiles[i:i+16], tx['tiles'][i:i+16])
            mask = bands.core_mask(font, label)
            before = rgba_crop(decode_texture(tx), tx['width'], label['rect'])
            after = rgba_crop(decode_texture(tx, tiles), tx['width'], label['rect'])
            expected = render_label(font, revise(label, [56]))
            def error(pixels):
                return sum(sum((pixels[i*4+k]-expected[i*4+k])**2 for k in range(3))
                           for i, alpha in enumerate(mask) if alpha >= 240)
            self.assertLess(error(after), error(before))
            self.assertEqual(bands.repair(tx, label, font, [56])[0], tiles)
            modified, _ = replace_tiles(data, sha(data), obj, tiles, [label['rect']], stored_decoder)
            restored, _ = replace_tiles(modified, sha(modified), obj, tx['tiles'], [label['rect']], stored_decoder)
            self.assertEqual(restored, data)

    def test_only_band_and_one_row_guard_blocks_are_eligible(self):
        with tempfile.TemporaryDirectory() as root:
            data, obj, label, font = self.fixture(root)
            tx = selected(data, obj, stored_decoder)[3]
            tiles, proof = bands.repair(tx, label, font, [56])
            before = render_label(font, label); after = render_label(font, revise(label, [56]))
            w, h = label['rect'][2:]; units = rect_units(tx['layout'], label['rect'])
            for j in range(h//4):
                for i in range(w//4):
                    changed = any(before[(y*w+x)*4:(y*w+x)*4+3] != after[(y*w+x)*4:(y*w+x)*4+3]
                                  for y in range(j*4, j*4+4) for x in range(i*4, i*4+4))
                    guard = set(range(j*4, j*4+4)) & set(proof['guard_rows'])
                    if not changed and not guard:
                        at = units[j*(w//4)+i]
                        self.assertEqual(tiles[at:at+16], tx['tiles'][at:at+16])

    def test_opaque_backdrop_is_not_replaced_by_transparent_text(self):
        with tempfile.TemporaryDirectory() as root:
            data, obj, label, font = self.fixture(root)
            tx = selected(data, obj, stored_decoder)[3]
            # Fully opaque native alpha, including outside the foreground mask.
            native = bytearray(tx['tiles'])
            for at in range(0, len(native), 16):
                native[at:at+8] = bytes([255, 255])+bytes(6)
            tx = dict(tx, tiles=bytes(native))
            tiles, _ = bands.repair(tx, label, font, [56])
            self.assertEqual(set(decode_texture(tx, tiles)[3::4]), {255})
            self.assertEqual(decode_texture(tx)[3::4], decode_texture(tx, tiles)[3::4])

    def test_bad_gradient_or_format_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            data, obj, label, font = self.fixture(root)
            tx = selected(data, obj, stored_decoder)[3]
            for positions in ([], [0], [1000], [56, 56], [55]):
                with self.assertRaises(ValueError):
                    bands.repair(tx, label, font, positions)
            wrong = dict(tx, layout=dict(tx['layout'], format=5))
            with self.assertRaises(ValueError):
                bands.repair(wrong, label, font, [56])
            for rows in ([-1], [28], [2, 2], [True]):
                with self.assertRaises(ValueError):
                    bands.repair(tx, label, font, [], rows)
            translucent = copy.deepcopy(label)
            translucent['appearance']['gradient'][0][1][3] = 180
            with self.assertRaises(ValueError):
                bands.repair(tx, translucent, font, [56])

    def test_native_quantization_only_repair_does_not_edit_palette_recipe(self):
        with tempfile.TemporaryDirectory() as root:
            data, obj, label, font = self.fixture(root)
            tx = selected(data, obj, stored_decoder)[3]
            snapshot = copy.deepcopy(label)
            tiles, proof = bands.repair(tx, label, font, [], [5])
            self.assertEqual(label, snapshot)
            self.assertEqual(proof['removed_gradient_positions'], [])
            self.assertEqual(decode_texture(tx)[3::4], decode_texture(tx, tiles)[3::4])

    def test_row_reader_does_not_misclassify_a_deliberate_ramp(self):
        mask = bytes([255])*20
        ramp = b''.join(bytes([v, v, v, 255])*4 for v in [250, 230, 210, 190, 170])
        self.assertEqual(bands.dark_rows(ramp, mask, 4), [])

    def test_screen_detects_a_narrow_two_sample_dark_plateau_not_a_wide_fade(self):
        label = dict(appearance=dict(ink_box=[0,0,128,28], gradient=[
            [0,[255]*4], [778,[255]*4], [815,[145]*4],
            [852,[145]*4], [889,[255]*4], [1000,[255]*4]]))
        self.assertEqual(bands.narrow_gradient_positions(label), [815,852])
        label['appearance']['gradient'][1][0] = 500
        self.assertEqual(bands.narrow_gradient_positions(label), [])

    def test_outline_rgb_leakage_repair_preserves_alpha_and_every_other_block(self):
        with tempfile.TemporaryDirectory() as root:
            data,obj,label,font = self.fixture(root)
            tx = selected(data,obj,stored_decoder)[3]; units = set(rect_units(tx['layout'],label['rect']))
            # Simulate a bright minimum palette endpoint while retaining the
            # original glyph/outline alpha and source-font geometry exactly.
            damaged = bytearray(tx['tiles'])
            for at in units:
                block = tx['tiles'][at:at+16]
                linear = b''.join(block[k:k+2][::-1] for k in range(0,16,2))
                c0,c1,indices = struct.unpack('<HHI',linear[8:])
                if c1 < 0x4208 < c0:
                    linear = linear[:8]+struct.pack('<HHI',c0,0x4208,indices)
                    damaged[at:at+16] = b''.join(linear[k:k+2][::-1] for k in range(0,16,2))
            broken = dict(tx,tiles=bytes(damaged)); snapshot = copy.deepcopy(label)
            fixed,proof = bands.repair_dark_outline(broken,label,font)
            self.assertGreater(proof['bright_outline_pixels_before'],0)
            self.assertLess(proof['bright_outline_pixels_after'],proof['bright_outline_pixels_before'])
            self.assertEqual(label,snapshot)
            self.assertEqual(decode_texture(broken)[3::4],decode_texture(broken,fixed)[3::4])
            for at in range(0,len(fixed),16):
                self.assertEqual(fixed[at:at+8],damaged[at:at+8])
                if at not in units:self.assertEqual(fixed[at:at+16],damaged[at:at+16])
            self.assertEqual(bands.repair_dark_outline(broken,label,font)[0],fixed)

    def test_detector_can_fail_and_pass_on_same_owned_stroke_geometry(self):
        mask = bytes([255])*20
        broken = b''.join(bytes([v, v, v, 255])*4 for v in [250, 250, 140, 250, 250])
        fixed = bytes([250, 250, 250, 255])*20
        self.assertEqual(bands.dark_rows(broken, mask, 4), [2])
        self.assertEqual(bands.dark_rows(fixed, mask, 4), [])
        with self.assertRaises(ValueError):
            bands.row_means(fixed, mask[:-1], 4)

    def test_native_explicit_samples_detect_plateau_and_bright_outline(self):
        from tools.audit_texture_dark_bands import rgb_samples
        mask=bytes([255])*20
        broken=b''.join(bytes([v,v,v,255])*4 for v in [250,140,140,250,250])
        fixed=bytes([250,250,250,255])*20
        spec=dict(kind='core-row-red-min',rows=[1,2],minimum=232)
        self.assertFalse(rgb_samples(broken,mask,4,spec)['passed'])
        self.assertTrue(rgb_samples(fixed,mask,4,spec)['passed'])
        edge=dict(kind='outline-rgb-max',points=[[1,1]],maximum=32,minimum_alpha=128)
        self.assertFalse(rgb_samples(fixed,mask,4,edge)['passed'])
        self.assertTrue(rgb_samples(bytes([8,8,8,147])*20,mask,4,edge)['passed'])
        self.assertFalse(rgb_samples(bytes([8,8,8,0])*20,mask,4,edge)['passed'])
        with self.assertRaises(ValueError):rgb_samples(fixed,mask,4,dict(spec,rows=[5]))

    def test_builder_rejects_duplicate_and_undeclared_changes(self):
        profile = dict(schema_version=1, kind='native-rgb-band-repair-v1', label_plans=[],
                       prior_gradient_revisions=[], requests=[dict(id='a', remove_gradient_positions=[56])],
                       resources=[dict(path='a.xxx', sha256='0'*64, discs=[1, 2],
                         textures=[dict(object='a', tiled_sha256='0'*64, labels=['a'])])])
        self.assertEqual(builder.validate(profile)['a']['remove_gradient_positions'], [56])
        cases = []
        p = copy.deepcopy(profile); p['requests'] *= 2; cases.append(p)
        p = copy.deepcopy(profile); p['resources'] *= 2; cases.append(p)
        p = copy.deepcopy(profile); p['resources'][0]['textures'][0]['labels'] = ['unknown']; cases.append(p)
        p = copy.deepcopy(profile); p['resources'][0]['discs'] = [3]; cases.append(p)
        p = copy.deepcopy(profile); p['requests'][0]['restore_outline_rgb'] = 1; cases.append(p)
        for p in cases:
            with self.assertRaises(ValueError):
                builder.validate(p)

    def test_builder_rebuilds_and_hash_guards_a_real_package_copy(self):
        from tools.runtime_envelope import ALIGNMENT
        with tempfile.TemporaryDirectory() as root:
            root = Path(root); data, obj, label, font = self.fixture(root)
            data += bytes((-len(data)) % ALIGNMENT)
            source = root/'input'; source.mkdir(); (source/'a.xxx').write_bytes(data)
            tx = selected(data, obj, None)[3]
            profile = dict(schema_version=1, kind='native-rgb-band-repair-v1',
                label_plans=[dict(path='labels.json', sha256=sha((root/'labels.json').read_bytes()))],
                prior_gradient_revisions=[], requests=[dict(id='owned', remove_gradient_positions=[56])],
                resources=[dict(path='a.xxx', sha256=sha(data), discs=[1, 2],
                    textures=[dict(object=obj, tiled_sha256=sha(tx['tiles']), labels=['owned'])])])
            first = builder.build(profile, root, source, root/'first')
            second = builder.build(profile, root, source, root/'second')
            self.assertEqual(first, second)
            self.assertEqual((root/'first/candidate/a.xxx').read_bytes(),
                             (root/'second/candidate/a.xxx').read_bytes())
            self.assertEqual((source/'a.xxx').read_bytes(), data)
            self.assertNotEqual((root/'first/candidate/a.xxx').read_bytes(), data)
            from tools.audit_texture_dark_bands import audit
            checked = audit(profile, root, source, root/'first/candidate', first, 'owned')
            self.assertTrue(checked['native_alpha_identical'])
            baseline_check = audit(profile, root, source, source, first, 'owned')
            self.assertFalse(baseline_check['passed'])
            from tools.screen_texture_dark_bands import screen
            plan = json.loads((root/'labels.json').read_bytes())
            plan['sources'] = [dict(path='a.xxx', textures=[dict(object=obj, label='owned')])]
            (root/'screen-labels.json').write_text(json.dumps(plan), encoding='utf8')
            screen_profile = copy.deepcopy(profile)
            screen_profile['label_plans'] = [dict(path='screen-labels.json',
                sha256=sha((root/'screen-labels.json').read_bytes()))]
            recipe = dict(discs=[dict(resources=[dict(path='a.xxx', file=str(source/'a.xxx'), sha256=sha(data))])])
            report = screen(screen_profile, recipe, root)
            self.assertEqual(report['screened'], 1)
            self.assertEqual(report['rows'][0]['gradient_positions'], [56])
            revised = screen(screen_profile, recipe, root, apply_revision=True)
            self.assertEqual(revised['rows'][0]['gradient_positions'], [])
            # Per-disc TOCs may differ; unrelated resources are not lettering.
            two_disc = copy.deepcopy(recipe)
            two_disc['discs'].append(copy.deepcopy(two_disc['discs'][0]))
            for disc, digest in zip(two_disc['discs'], ('a'*64, 'b'*64)):
                disc['resources'].append(dict(path='Xbox360TOC.txt', sha256=digest))
            self.assertEqual(screen(screen_profile, two_disc, root)['screened'], 1)
            two_disc['discs'][1]['resources'][0]['sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'different disc candidates'):
                screen(screen_profile, two_disc, root)
            # Changing even one alpha byte is detected independently of the
            # expected whole-file hash, so an updated manifest cannot hide it.
            path = root/'first/candidate/a.xxx'; altered = bytearray(path.read_bytes())
            c, e, _, texture = selected(bytes(altered), obj, None)
            at = e['serial_offset']+texture['payload_offset']+rect_units(texture['layout'], label['rect'])[0]
            altered[at] ^= 1; path.write_bytes(altered)
            spoof = copy.deepcopy(first); spoof['resources'][0]['sha256'] = sha(bytes(altered))
            checked = audit(profile, root, source, root/'first/candidate', spoof, 'owned')
            self.assertFalse(checked['native_alpha_identical'])
            self.assertFalse(checked['passed'])
            for disc in (1, 2):
                self.assertEqual(json.loads((root/f'first/replacements-disc{disc}.json').read_bytes())['disc'], disc)
            wrong = copy.deepcopy(profile); wrong['resources'][0]['sha256'] = '0'*64
            with self.assertRaises(ValueError):
                builder.build(wrong, root, source, root/'bad')
            self.assertFalse((root/'bad').exists())
            with self.assertRaises(ValueError):
                builder.build(profile, root, source, source/'nested')


if __name__ == '__main__':
    unittest.main()
