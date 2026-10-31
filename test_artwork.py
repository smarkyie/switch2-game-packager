"""Artwork codec, crop geometry, and non-destructive normalization tests."""
from pathlib import Path
import hashlib,io,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).parent/'src'))
from PIL import Image,ImageDraw
from artwork import ArtworkSelection,CropModel,artwork_bytes

class ArtworkTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).parent/'test-work';scratch.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='art-',dir=scratch);self.root=Path(self.temp.name)
        self.image=Image.new('RGB',(800,400),'red');d=ImageDraw.Draw(self.image)
        d.rectangle((200,0,599,399),fill='green');d.rectangle((600,0,799,399),fill='blue')
    def tearDown(self):self.temp.cleanup()
    def test_center_and_positioned_crop(self):
        p=self.root/'wide.png';self.image.save(p);before=hashlib.sha256(p.read_bytes()).hexdigest()
        with Image.open(io.BytesIO(artwork_bytes(p))) as im:
            self.assertEqual(im.size,(256,256));self.assertGreater(im.getpixel((128,128))[1],90)
        model=CropModel(800,400);model.set_zoom(3);model.pan(330,0)
        data=artwork_bytes(ArtworkSelection(p,model.box()))
        with Image.open(io.BytesIO(data)) as im:self.assertGreater(im.getpixel((128,128))[2],200)
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),before)
    def test_fit_whole_image_retained(self):
        p=self.root/'wide.webp';self.image.save(p)
        with Image.open(io.BytesIO(artwork_bytes(ArtworkSelection(p,fit=True)))) as im:
            self.assertEqual(im.size,(256,256));self.assertTrue(all(n>245 for n in im.getpixel((128,4))))
    def test_supported_codecs(self):
        for ext,fmt in [('webp','WEBP'),('gif','GIF'),('tiff','TIFF'),('bmp','BMP'),('ico','ICO'),('icns','ICNS'),('avif','AVIF'),('jp2','JPEG2000')]:
            with self.subTest(format=fmt):
                p=self.root/('icon.'+ext);image=self.image.resize((256,256))
                image.save(p,format=fmt)
                with Image.open(io.BytesIO(artwork_bytes(p))) as im:self.assertEqual(im.size,(256,256));self.assertEqual(im.format,'JPEG')
    def test_invalid_crop_refused(self):
        p=self.root/'wide.png';self.image.save(p)
        for box in [(-.1,0,1,1),(0,0,1,1),(1,1,0,0),(0,0,float('nan'),1)]:
            with self.subTest(box=box),self.assertRaises(ValueError):artwork_bytes(ArtworkSelection(p,box))

if __name__=='__main__':unittest.main(verbosity=2)
