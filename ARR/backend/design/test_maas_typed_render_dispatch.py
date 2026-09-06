"""End-to-end raster regression: explicit top and underside reach rendering."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import SimpleTestCase
from PIL import Image, ImageChops
from shapely.geometry import box
from design.maas.source_geometry.ir import SourceMass, SourceVolume
from design.maas.source_geometry.solid import AffineSurface, ConstantSurface, PolynomialSurface
from design.maas.massv2.render import render_masses


class TypedRenderDispatchTests(SimpleTestCase):
    def test_typed_upper_and_lower_cuts_change_solid_pixels(self):
        prism=SourceVolume('body',box(0,0,10,10),0,1,'fixture')
        fields=[{'top_surface':PolynomialSurface(((0,0,.3),(1,0,.07)))},
                {'top_surface':ConstantSurface(1),'bottom_surface':ConstantSurface(.6)}]
        with TemporaryDirectory() as folder:
            def raster(v,key):
                source=SourceMass('same',v.footprint,volumes=(v,),metadata={'authored_height_m':10})
                path=Path(folder)/f'{key}.png'
                render_masses([('same',source,{})],path,columns=1,tile=(400,360))
                return Image.open(path).convert('RGB')
            full=raster(prism,'full')
            exact_prism=replace(prism,
                top_surface=AffineSurface(ConstantSurface(1),(2,0,0,2,7,9)),
                bottom_surface=AffineSurface(ConstantSurface(0),(2,0,0,2,7,9)))
            self.assertIsNone(ImageChops.difference(full,raster(exact_prism,'explicit-flat')).getbbox())
            for i,field in enumerate(fields):
                with self.subTest(surface=field):
                    cut=raster(replace(prism,**field),str(i))
                    changed=sum(any(p) for p in ImageChops.difference(full,cut).getdata())
                    self.assertGreater(changed,1000)
                    # Removed material must expose background in the drawing,
                    # not merely change an internal triangulation line.
                    background=full.getpixel((399,359))
                    exposed=sum(p!=background and q==background for p,q in zip(full.getdata(),cut.getdata()))
                    self.assertGreater(exposed,500)
