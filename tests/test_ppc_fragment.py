"""Self-authored synthetic PPC fragments; no game, GPU or assembler required."""
import struct
import unittest

from tools.ppc_fragment import FragmentError,MemorySegment,canonical_address,run_fragment

BASE=0x82000000
MASK64=(1<<64)-1


def d(op,rt,ra,imm):return op<<26|rt<<21|ra<<16|(imm&65535)
def x(rt,ra,rb,xo,rc=0):return 31<<26|rt<<21|ra<<16|rb<<11|xo<<1|rc
def compare(op,field,ra,operand):return op<<26|field<<23|ra<<16|(operand&65535)
def rotate(ra,rs,sh,mb,me,rc=0):return 21<<26|rs<<21|ra<<16|sh<<11|mb<<6|me<<1|rc
def branch(delta,link=0):return 18<<26|(delta&0x03fffffc)|link
def conditional(delta,bo=12,bi=26):return 16<<26|bo<<21|bi<<16|(delta&0xfffc)
def image(*words):return b''.join(struct.pack('>I',w) for w in words)


def execute(words,regs=None,memory=(),**kwargs):
    b=image(*words);end=BASE+len(b)
    return run_fragment(b,BASE,(BASE,end),BASE,{end},regs or {},memory,**kwargs)


class FragmentTests(unittest.TestCase):
    def test_li_lis_addi_addis_ori_and_unknown_r0_distinction(self):
        r=execute([d(14,3,0,-1),d(15,4,0,0x8321),d(14,4,4,-0x5268),d(24,3,5,0x1234)])
        self.assertEqual(r.registers[3],MASK64)
        self.assertEqual(r.registers[4],0xffffffff8320ad98)
        self.assertEqual(r.registers[5],MASK64)
        self.assertIsNone(r.carry)
        self.assertEqual(r.trace,tuple(BASE+i*4 for i in range(4)))
        with self.assertRaisesRegex(FragmentError,'unknown register r0'):execute([d(12,3,0,1)])

    def test_64bit_addic_carry_and_subfe_same_operand(self):
        for v,want_carry,want in [(0,False,MASK64),(1,True,0),(0x100000000,True,0)]:
            r=execute([d(12,3,3,-1),x(4,3,3,136)],{3:v})
            self.assertEqual(r.registers[4],want)
            self.assertEqual(r.carry,want_carry)
        r=execute([d(12,5,3,1)],{3:0xffffffff})
        self.assertEqual(r.registers[5],0x100000000)
        self.assertFalse(r.carry)  # Explicitly 64-bit, not carry-out of bit31.

    def test_unknown_carry_and_overflow_forms_are_rejected(self):
        with self.assertRaisesRegex(FragmentError,'unknown carry'):execute([x(3,4,5,136)],{4:1,5:2})
        for xo in (136|512,266|512):
            with self.assertRaises(FragmentError):execute([x(3,4,5,xo)],{4:1,5:2})

    def test_compare_signed_and_unsigned_word_ignores_upper_bits(self):
        r=execute([compare(11,6,3,0),compare(10,5,3,1)],{3:0x12345678ffffffff})
        self.assertTrue(r.cr_bits[24]);self.assertFalse(r.cr_bits[25]);self.assertFalse(r.cr_bits[26])
        self.assertTrue(r.cr_bits[21]);self.assertNotIn(27,r.cr_bits)
        r=execute([x(6<<2,3,4,0),x(5<<2,3,4,32)],{3:MASK64,4:1})
        self.assertTrue(r.cr_bits[24]);self.assertTrue(r.cr_bits[21])

    def test_comparison_reserved_long_and_record_forms_fail(self):
        bad=[compare(11,6,3,0)|(1<<21),compare(10,6,3,0)|(1<<22),x(6<<2,3,4,0,1)]
        for word in bad:
            with self.assertRaises(FragmentError):execute([word],{3:1,4:2})

    def test_true_and_false_bc_and_relative_b_to_explicit_stop(self):
        for value,bo,expected in [(0,12,9),(1,12,4),(0,4,4),(1,4,9)]:
            r=execute([compare(11,6,3,0),conditional(12,bo),d(14,4,0,4),branch(8),d(14,4,0,9)],{3:value})
            self.assertEqual(r.registers[4],expected)
        r=run_fragment(image(branch(0x100)),BASE,(BASE,BASE+4),BASE,{BASE+0x100},{})
        self.assertEqual(r.stop_pc,BASE+0x100)

    def test_unknown_cr_ctr_absolute_link_and_window_escape_rejected(self):
        for word in [conditional(4),conditional(4,bo=16),branch(4,1),branch(4)|2,conditional(4)|1]:
            with self.subTest(word=hex(word)),self.assertRaises(FragmentError):execute([word])
        with self.assertRaisesRegex(FragmentError,'escaped window'):execute([branch(8)])

    def test_rotate_mask_including_ppc64_wrapping_mask_and_record(self):
        r=execute([rotate(4,3,8,16,23),rotate(5,3,0,28,3),rotate(6,3,0,0,31,1)],{3:0xfedcba9812345678})
        self.assertEqual(r.registers[4],0x7800)
        self.assertEqual(r.registers[5],0x1234567810000008)
        self.assertEqual(r.registers[6],0x12345678)
        self.assertTrue(r.cr_bits[1]);self.assertFalse(r.cr_bits[0]);self.assertNotIn(3,r.cr_bits)
        r=execute([rotate(4,3,0,0,31,1)],{3:0x80000000})
        self.assertTrue(r.cr_bits[1])  # Zero-extended 32-bit result is positive in PPC64.
        r=execute([rotate(4,3,0,0,31,1)],{3:0})
        self.assertTrue(r.cr_bits[2])

    def test_or_and_record_are_64bit(self):
        r=execute([x(3,5,4,444),x(3,6,4,28,1)],{3:MASK64,4:0x8000000000000001})
        self.assertEqual(r.registers[5],MASK64)
        self.assertEqual(r.registers[6],0x8000000000000001)
        self.assertTrue(r.cr_bits[0])

    def test_rotate_mask_bitstring_reference_matrix(self):
        source=0xa1907ef3
        for sh in [0,1,7,31]:
            bits=f'{source:032b}'*2
            rotated=bits[sh:]+bits[:sh]
            for mb,me in [(0,31),(4,6),(28,3),(31,0),(0,0),(31,31)]:
                begin,end=mb+32,me+32
                kept=''.join(v if (begin<=i<=end if begin<=end else i>=begin or i<=end)
                             else '0' for i,v in enumerate(rotated))
                r=execute([rotate(4,3,sh,mb,me,1)],{3:source})
                expected=int(kept,2)
                with self.subTest(sh=sh,mb=mb,me=me):
                    self.assertEqual(r.registers[4],expected)
                    self.assertEqual(r.cr_bits[0],bool(expected&(1<<63)))
                    self.assertEqual(r.cr_bits[2],expected==0)

    def test_indexed_zero_base_and_load_zero_extension(self):
        r=execute([x(3,0,4,23)],{4:0x90000000},[MemorySegment(0x90000000,bytes.fromhex('ffffffff'))])
        self.assertEqual(r.registers[3],0xffffffff)

    def test_halfword_load_update_indexed_store_and_zero_extension(self):
        raw=bytes.fromhex('1234ffff0000');a=0x90000000
        r=execute([d(40,3,4,2),d(41,5,4,2),x(6,0,4,279),d(44,7,4,2)],
                  {4:a,7:0xabcdef129876},[MemorySegment(a,raw,True)])
        self.assertEqual((r.registers[3],r.registers[5],r.registers[6]),(65535,65535,65535))
        self.assertEqual(r.registers[4],a+2)
        self.assertEqual(r.segments[0].data,bytes.fromhex('1234ffff9876'))
        self.assertEqual(r.stores,((a+4,0x9876),))
        self.assertEqual(raw,bytes.fromhex('1234ffff0000'))

    def test_indexed_byte_widen_and_halfword_store_are_unsigned_bounded(self):
        a=0x90000000;out=0x90000100
        for value in (0,0x7f,0x80,0xa9,0xff):
            raw=bytes([0x11,value]);r=execute([x(3,4,5,87),x(3,0,6,407)],
                {4:a,5:1,6:out},[MemorySegment(a,raw),MemorySegment(out,b'xx',True)])
            self.assertEqual(r.registers[3],value)
            self.assertEqual(r.segments[1].data,bytes([0,value]))
            self.assertEqual(r.segments[0].data,raw)
        r=execute([x(3,0,4,87)],{4:a+1},[MemorySegment(a,b'\x00\xff')])
        self.assertEqual(r.registers[3],255)
        for word,regs in [(x(3,4,5,87,1),{4:a,5:1}),
                (x(3,4,5,87),{4:a,5:2}), (x(3,0,4,407,1),{3:1,4:a}),
                (x(3,0,4,407),{3:1,4:a+1})]:
            with self.subTest(word=word),self.assertRaises(FragmentError):
                execute([word],regs,[MemorySegment(a,b'xy',True)])
        with self.assertRaisesRegex(FragmentError,'read-only'):
            execute([x(3,0,4,407)],{3:0xa9,4:a},[MemorySegment(a,b'xy')])

    def test_halfword_invalid_updates_alignment_bounds_and_record_fail(self):
        for word in [d(41,3,0,0),d(41,3,3,0),x(3,4,5,279,1),
                     d(40,3,4,1),d(40,3,4,2),d(44,3,4,1),d(44,3,4,2)]:
            with self.subTest(word=hex(word)),self.assertRaises(FragmentError):
                execute([word],{3:0,4:0x90000000,5:0},[MemorySegment(0x90000000,b'123',True)])
        with self.assertRaisesRegex(FragmentError,'read-only'):
            execute([d(44,3,4,0)],{3:1,4:0x90000000},[MemorySegment(0x90000000,b'ab')])

    def test_subf_record_and_signed_word_immediate_shift(self):
        r=execute([x(5,3,4,40,1)],{3:8,4:3})
        self.assertEqual(r.registers[5],MASK64-4);self.assertTrue(r.cr_bits[0])
        for source,shift,want,carry in [(8,1,4,False),(0xffffffff,1,MASK64,True),
                (0xfffffffe,1,MASK64,False),(0x80000000,31,MASK64,False),
                (0x1234567880000001,0,0xffffffff80000001,False),
                (0x1234567880000001,31,MASK64,True)]:
            r=execute([x(3,4,shift,824,1)],{3:source})
            self.assertEqual(r.registers[4],want);self.assertEqual(r.carry,carry)
            self.assertEqual(r.cr_bits[0],bool(want&(1<<63)))
        with self.assertRaises(FragmentError):execute([x(5,3,4,40|512)],{3:8,4:3})

    def test_store_alignment_boundary_and_unknown_source_fail(self):
        for word,regs,data in [
            (d(36,3,4,1),{3:1,4:0x90000000},bytes(8)),
            (d(36,3,4,4),{3:1,4:0x90000000},bytes(7)),
            (d(36,3,4,0),{4:0x90000000},bytes(8)),
        ]:
            with self.subTest(regs=regs),self.assertRaises(FragmentError):
                execute([word],regs,[MemorySegment(0x90000000,data,True)])

    def test_signed_canonical_image_loads_and_raw_lfs(self):
        b=image(d(15,3,0,0x8200),d(32,4,3,12),d(48,7,3,12),0x7fc01234)
        r=run_fragment(b,BASE,(BASE,BASE+12),BASE,{BASE+12},{})
        self.assertEqual(r.registers[4],0x7fc01234);self.assertEqual(r.fpr_bits,{7:0x7fc01234})
        self.assertEqual(canonical_address(0xffffffff82000000),BASE)
        for bad in (0x1234567882000000,0xffffffff00000010):
            with self.assertRaisesRegex(FragmentError,'noncanonical'):canonical_address(bad)

    def test_synthetic_stores_stwu_indexed_load_and_add(self):
        data=bytearray(16);source_regs={1:0xffffffff90000008,3:0x12345678,4:4,6:0x90000000}
        segment=MemorySegment(0x90000000,data,True)
        r=execute([d(37,1,1,-8),d(36,3,6,4),x(5,6,4,23),x(7,5,4,266)],source_regs,[segment])
        self.assertEqual(r.registers[1],0xffffffff90000000)
        self.assertEqual(r.registers[5],0x12345678);self.assertEqual(r.registers[7],0x1234567c)
        self.assertEqual(r.segments[0].data[:8],bytes.fromhex('9000000812345678'))
        self.assertEqual(r.stores,((0x90000000,0x90000008),(0x90000004,0x12345678)))
        self.assertEqual(data,bytes(16));self.assertEqual(source_regs[1],0xffffffff90000008)
        self.assertIsInstance(r.segments,tuple);self.assertIsInstance(r.segments[0].data,bytes)

    def test_add_record_indexed_load_record_and_stwu_r0_are_rejected(self):
        for word in [x(3,4,5,266,1),x(3,4,5,23,1),d(37,3,0,0)]:
            with self.assertRaises(FragmentError):execute([word],{3:1,4:2,5:3})

    def test_unknown_register_memory_unaligned_and_boundary_reads_fail(self):
        for word,regs,memory in [
            (d(14,3,4,1),{},()),(d(32,3,4,0),{4:0x90000000},()),
            (d(32,3,4,1),{4:BASE},()),
            (d(32,3,4,4),{4:0x90000000},(MemorySegment(0x90000000,b'1234567'),)),
            (d(32,3,4,0),{4:0x1234567882000000},()),
        ]:
            with self.subTest(word=hex(word)),self.assertRaises(FragmentError):execute([word],regs,memory)

    def test_image_and_readonly_segment_stores_fail_without_mutation(self):
        code=bytearray(image(d(36,3,4,0)));original=bytes(code)
        with self.assertRaisesRegex(FragmentError,'image is read-only'):
            run_fragment(code,BASE,(BASE,BASE+4),BASE,{BASE+4},{3:0,4:BASE})
        self.assertEqual(code,original)
        with self.assertRaisesRegex(FragmentError,'read-only'):
            execute([d(36,3,4,0)],{3:0,4:0x90000000},[MemorySegment(0x90000000,b'abcd')])
        with self.assertRaisesRegex(FragmentError,'unknown memory write'):
            execute([d(36,3,4,0)],{3:0,4:0x90000000})

    def test_overlapping_segments_image_overlap_and_wrapping_ranges_fail(self):
        for memory in [
            [MemorySegment(BASE,b'abcd')],
            [MemorySegment(0x90000000,b'12345'),MemorySegment(0x90000004,b'4567')],
            [MemorySegment(0xfffffffc,b'12345678')],
        ]:
            with self.assertRaises(FragmentError):execute([d(14,3,0,1)],memory=memory)

    def test_budget_unknown_instruction_and_external_call_fail_closed(self):
        with self.assertRaisesRegex(FragmentError,'budget'):execute([branch(0)],max_steps=8)
        execute([d(14,3,0,1)],max_steps=1)
        for budget in [0,257,True]:
            with self.assertRaises(FragmentError):execute([d(14,3,0,1)],max_steps=budget)
        for word in [0,0x4e800020,0x4e800421,0x48000005]:
            with self.assertRaises(FragmentError):execute([word])

    def test_invalid_entry_window_stop_and_register_inputs_fail(self):
        b=image(d(14,3,0,1))
        for kwargs in [dict(base=BASE+1),dict(window=(BASE+4,BASE)),dict(entry=BASE+4),
                       dict(stops=set()),dict(stops={BASE+5}),dict(registers={32:1}),
                       dict(registers={3:True}),dict(registers={3:1<<64})]:
            args=dict(image=b,base=BASE,window=(BASE,BASE+4),entry=BASE,stops={BASE+4},registers={})
            args.update(kwargs)
            with self.subTest(kwargs=kwargs),self.assertRaises(FragmentError):run_fragment(**args)


if __name__=='__main__':unittest.main()
