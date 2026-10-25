import io
import pytest
from fastapi import HTTPException
from PIL import Image
from backend.app.modules.media.security import owned_path, process_photo, MAX_BYTES


def picture(fmt='PNG', size=(300, 600)):
    im = Image.new('RGB', size, '#8e6ad0')
    with io.BytesIO() as output:
        im.save(output, format=fmt)
        return output.getvalue()


def test_valid_image_canonical_webp_without_exif():
    raw = process_photo(picture(), 'image/png')
    with Image.open(io.BytesIO(raw)) as image:
        assert image.format == 'WEBP'
        assert image.size == (512, 512)
        assert not image.getexif()

@pytest.mark.parametrize('data,ctype,code', [
    (b'', 'image/png', 400),
    (b'<script>bad</script>', 'image/png', 400),
    (picture(), 'text/html', 415),
    (picture(), 'image/jpeg', 415),
    (b'X' * (MAX_BYTES + 1), 'image/png', 413),
])
def test_bad_upload_rejected(data, ctype, code):
    if ctype == 'image/jpeg' and data.startswith(b'\x89PNG'):
        # Format mismatch should be blocked (not just MIME allow-listed).
        with pytest.raises(HTTPException) as ex:
            process_photo(data, ctype)
        assert ex.value.status_code == code
        return
    with pytest.raises(HTTPException) as ex:
        process_photo(data, ctype)
    assert ex.value.status_code == code


def test_paths_only_allow_generated_keys(tmp_path):
    assert owned_path(tmp_path, '/api/media/profile-photos/'+'f'*32+'.webp') == tmp_path / ('f'*32+'.webp')
    for bad in ['/etc/passwd', '/api/media/profile-photos/../oops.webp',
                '/api/media/profile-photos/'+'a'*32+'.png',
                '/api/media/profile-photos/'+'a'*32+'.webp?x=1']:
        assert owned_path(tmp_path, bad) is None
