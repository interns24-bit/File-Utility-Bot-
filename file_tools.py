import os
import shutil
import subprocess
import sys
import uuid

from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
import pymupdf


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


SUPPORTED_MEDIA_HOSTS = (
    "youtube.com",
    "youtu.be",
    "tiktok.com",
)


def create_output_path(
    original_path,
    extension
):

    original_name = Path(
        original_path
    ).stem


    unique_id = uuid.uuid4().hex[:6]


    filename = (
        f"{original_name}_"
        f"{unique_id}"
        f"{extension}"
    )


    return os.path.join(
        OUTPUT_DIR,
        filename
    )


def convert_image(
    input_path,
    target_format
):

    target_format = (
        target_format.lower()
    )


    format_map = {

        "jpg": (
            "JPEG",
            ".jpg"
        ),

        "jpeg": (
            "JPEG",
            ".jpg"
        ),

        "png": (
            "PNG",
            ".png"
        ),

        "webp": (
            "WEBP",
            ".webp"
        )

    }


    if target_format not in format_map:

        raise ValueError(
            "Supported image formats: "
            "jpg, png, webp"
        )


    pillow_format, extension = (
        format_map[target_format]
    )


    output_path = create_output_path(
        input_path,
        extension
    )


    with Image.open(
        input_path
    ) as image:


        if pillow_format == "JPEG":

            image = image.convert(
                "RGB"
            )


            image.save(
                output_path,
                pillow_format,
                quality=95
            )


        elif pillow_format == "WEBP":

            if image.mode not in (
                "RGB",
                "RGBA"
            ):

                image = image.convert(
                    "RGB"
                )


            image.save(
                output_path,
                pillow_format,
                quality=95
            )


        else:

            if image.mode not in (
                "RGB",
                "RGBA"
            ):

                image = image.convert(
                    "RGB"
                )


            image.save(
                output_path,
                pillow_format
            )


    return output_path


def image_to_pdf(
    input_path
):

    output_path = create_output_path(
        input_path,
        ".pdf"
    )


    with Image.open(
        input_path
    ) as image:

        image = image.convert(
            "RGB"
        )


        image.save(
            output_path,
            "PDF",
            resolution=300.0
        )


    return output_path


def pdf_to_images(
    input_path
):

    base_name = Path(
        input_path
    ).stem


    unique_id = uuid.uuid4().hex[:6]


    output_paths = []


    document = pymupdf.open(
        input_path
    )


    try:

        for page_number, page in enumerate(
            document
        ):


            pixmap = page.get_pixmap(
                dpi=200,
                colorspace=pymupdf.csRGB
            )


            filename = (
                f"{base_name}_"
                f"{unique_id}_"
                f"page_{page_number + 1}.png"
            )


            image_path = os.path.join(
                OUTPUT_DIR,
                filename
            )


            pixmap.save(
                image_path
            )


            output_paths.append(
                image_path
            )


    finally:

        document.close()


    return output_paths


def run_ffmpeg(
    command
):

    if shutil.which(
        "ffmpeg"
    ) is None:

        raise RuntimeError(
            "FFmpeg is not installed."
        )


    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


    if result.returncode != 0:

        raise RuntimeError(
            result.stderr[-3000:]
        )


def audio_to_mp3(
    input_path
):

    output_path = create_output_path(
        input_path,
        ".mp3"
    )


    command = [

        "ffmpeg",

        "-y",

        "-i",
        input_path,

        "-vn",

        "-codec:a",
        "libmp3lame",

        "-q:a",
        "2",

        output_path

    ]


    run_ffmpeg(
        command
    )


    return output_path


def video_to_mp4(
    input_path
):

    output_path = create_output_path(
        input_path,
        ".mp4"
    )


    command = [

        "ffmpeg",

        "-y",

        "-i",
        input_path,

        "-map",
        "0:v:0",

        "-map",
        "0:a?",

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        output_path

    ]


    run_ffmpeg(
        command
    )


    return output_path


def is_supported_media_url(
    url
):

    try:

        parsed = urlparse(
            url.strip()
        )


        if parsed.scheme not in (
            "http",
            "https"
        ):

            return False


        hostname = (
            parsed.hostname
            or ""
        ).lower()


        for host in SUPPORTED_MEDIA_HOSTS:

            if hostname == host:

                return True


            if hostname.endswith(
                "." + host
            ):

                return True


        return False


    except Exception:

        return False


def download_media_link(
    url,
    target_format
):

    if not is_supported_media_url(
        url
    ):

        raise ValueError(
            "Please send a valid public "
            "YouTube or TikTok link."
        )


    target_format = (
        target_format.lower()
    )


    if target_format not in (
        "mp3",
        "mp4"
    ):

        raise ValueError(
            "Target format must be "
            "mp3 or mp4."
        )


    unique_id = (
        uuid.uuid4().hex[:10]
    )


    output_template = os.path.join(
        OUTPUT_DIR,
        f"link_{unique_id}.%(ext)s"
    )


    if target_format == "mp3":

        command = [

            sys.executable,

            "-m",
            "yt_dlp",

            "--no-playlist",

            "--extract-audio",

            "--audio-format",
            "mp3",

            "--audio-quality",
            "2",

            "--restrict-filenames",

            "-o",
            output_template,

            url

        ]


    else:

        command = [

            sys.executable,

            "-m",
            "yt_dlp",

            "--no-playlist",

            "-f",
            "bv*[ext=mp4]+ba[ext=m4a]/"
            "b[ext=mp4]/b",

            "--merge-output-format",
            "mp4",

            "--recode-video",
            "mp4",

            "--restrict-filenames",

            "-o",
            output_template,

            url

        ]


    result = subprocess.run(

        command,

        stdout=subprocess.PIPE,

        stderr=subprocess.PIPE,

        text=True

    )


    if result.returncode != 0:

        error_text = (
            result.stderr.strip()
        )


        if not error_text:

            error_text = (
                result.stdout.strip()
            )


        raise RuntimeError(
            error_text[-3000:]
        )


    output_files = list(

        Path(
            OUTPUT_DIR
        ).glob(
            f"link_{unique_id}.*"
        )

    )


    valid_files = [

        path

        for path in output_files

        if path.suffix.lower()
        == f".{target_format}"

    ]


    if not valid_files:

        raise RuntimeError(

            "yt-dlp finished but the "
            f"{target_format.upper()} file "
            "could not be found."

        )


    return str(
        valid_files[0]
    )
