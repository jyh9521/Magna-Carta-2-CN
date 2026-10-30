import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_tagged_fields import Fixture
from tools.audit_ui_geometry import audit


class GeometryContractTests(unittest.TestCase):
    def test_real_serialized_anchor_detects_regression(self):
        data, ctx, _ = Fixture().build()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sample.xxx').write_bytes(data)
            term=dict(package='sample',object='Scene.Label',field=[['Position',0],['Value',0]])
            plan=dict(schema_version=1,kind='ui-geometry-contracts',packages=dict(sample='sample.xxx'),
                      anchors=[dict(name='right edge',terms=[term,dict(term,field=[['Position',0],['Value',2]])],expected=130)])
            with patch('tools.audit_ui_geometry.context',return_value=ctx):
                self.assertTrue(audit(root,plan)['passed'])
                plan['anchors'][0]['expected']=140
                self.assertFalse(audit(root,plan)['passed'])
                bad=copy.deepcopy(ctx);bad['tables']['exports']*=2
                with patch('tools.audit_ui_geometry.context',return_value=bad),self.assertRaises(ValueError):
                    audit(root,plan)
    def test_native_alpha_outside_clip_fails(self):
        data,ctx,_=Fixture().build()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sample.xxx').write_bytes(data)
            plan=dict(schema_version=1,kind='ui-geometry-contracts',packages=dict(sample='sample.xxx'),anchors=[],
                      alpha_bounds=[dict(name='clip',package='sample',object='Texture',clip=[1,1,2,2])])
            tex=dict(width=4,height=4)
            with patch('tools.audit_ui_geometry.context',return_value=ctx),patch('tools.audit_ui_geometry.selected',return_value=(None,None,None,tex)):
                with patch('tools.audit_ui_geometry.decode_texture',return_value=bytes([255])*64):
                    self.assertFalse(audit(root,plan)['passed'])
                with patch('tools.audit_ui_geometry.decode_texture',return_value=bytes(64)):
                    self.assertTrue(audit(root,plan)['passed'])
