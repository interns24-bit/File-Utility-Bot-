import cv2
import os
import uuid
import numpy as np

from PIL import Image
from datetime import datetime


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

SCAN_DIR = os.path.join(
    BASE_DIR,
    "scans"
)


os.makedirs(
    SCAN_DIR,
    exist_ok=True
)


def order_points(points):

    rect = np.zeros(
        (4, 2),
        dtype="float32"
    )

    sums = points.sum(
        axis=1
    )

    differences = np.diff(
        points,
        axis=1
    )

    rect[0] = points[
        np.argmin(sums)
    ]

    rect[2] = points[
        np.argmax(sums)
    ]

    rect[1] = points[
        np.argmin(differences)
    ]

    rect[3] = points[
        np.argmax(differences)
    ]

    return rect


def four_point_transform(
    image,
    points
):

    rect = order_points(
        points
    )

    top_left, top_right, bottom_right, bottom_left = rect


    width_a = np.linalg.norm(
        bottom_right - bottom_left
    )

    width_b = np.linalg.norm(
        top_right - top_left
    )

    max_width = int(
        max(width_a, width_b)
    )


    height_a = np.linalg.norm(
        top_right - bottom_right
    )

    height_b = np.linalg.norm(
        top_left - bottom_left
    )

    max_height = int(
        max(height_a, height_b)
    )


    destination = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")


    matrix = cv2.getPerspectiveTransform(
        rect,
        destination
    )


    warped = cv2.warpPerspective(
        image,
        matrix,
        (
            max_width,
            max_height
        )
    )


    return warped


def find_document(
    image
):

    original_height, original_width = (
        image.shape[:2]
    )


    target_width = 1000


    ratio = (
        target_width
        / float(original_width)
    )


    resized_height = int(
        original_height * ratio
    )


    resized = cv2.resize(
        image,
        (
            target_width,
            resized_height
        )
    )


    gray = cv2.cvtColor(
        resized,
        cv2.COLOR_BGR2GRAY
    )


    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )


    edges = cv2.Canny(
        blurred,
        50,
        150
    )


    edges = cv2.dilate(
        edges,
        np.ones(
            (5, 5),
            np.uint8
        ),
        iterations=1
    )


    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        np.ones(
            (7, 7),
            np.uint8
        )
    )


    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )


    contours = sorted(
        contours,
        key=cv2.contourArea,
        reverse=True
    )


    frame_area = (
        resized.shape[0]
        * resized.shape[1]
    )


    for contour in contours:

        area = cv2.contourArea(
            contour
        )


        if area < frame_area * 0.20:
            continue


        perimeter = cv2.arcLength(
            contour,
            True
        )


        approximation = cv2.approxPolyDP(
            contour,
            0.02 * perimeter,
            True
        )


        if len(approximation) == 4:

            points = (
                approximation
                .reshape(4, 2)
                .astype(np.float32)
            )


            points /= ratio


            return points


    return None


def enhance_document(
    image
):

    lab = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2LAB
    )


    l_channel, a_channel, b_channel = (
        cv2.split(lab)
    )


    clahe = cv2.createCLAHE(
        clipLimit=1.8,
        tileGridSize=(8, 8)
    )


    l_channel = clahe.apply(
        l_channel
    )


    enhanced_lab = cv2.merge([
        l_channel,
        a_channel,
        b_channel
    ])


    enhanced = cv2.cvtColor(
        enhanced_lab,
        cv2.COLOR_LAB2BGR
    )


    blurred = cv2.GaussianBlur(
        enhanced,
        (0, 0),
        1.0
    )


    sharpened = cv2.addWeighted(
        enhanced,
        1.15,
        blurred,
        -0.15,
        0
    )


    return sharpened


def create_pdf(
    image,
    output_path
):

    rgb_image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )


    pil_image = Image.fromarray(
        rgb_image
    )


    pil_image.save(
        output_path,
        "PDF",
        resolution=300.0
    )


def scan_document(
    input_path
):

    if not os.path.exists(
        input_path
    ):

        raise FileNotFoundError(
            f"Input image not found: {input_path}"
        )


    frame = cv2.imread(
        input_path
    )


    if frame is None:

        raise ValueError(
            "Could not read the input image."
        )


    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


    unique_id = uuid.uuid4().hex[:6]


    base_name = (
        f"scan_{timestamp}_{unique_id}"
    )


    original_path = os.path.join(
        SCAN_DIR,
        f"{base_name}_original.jpg"
    )


    processed_path = os.path.join(
        SCAN_DIR,
        f"{base_name}.jpg"
    )


    pdf_path = os.path.join(
        SCAN_DIR,
        f"{base_name}.pdf"
    )


    cv2.imwrite(
        original_path,
        frame
    )


    document_points = find_document(
        frame
    )


    if document_points is not None:

        scanned = four_point_transform(
            frame,
            document_points
        )

    else:

        scanned = frame


    processed = enhance_document(
        scanned
    )


    cv2.imwrite(
        processed_path,
        processed
    )


    create_pdf(
        processed,
        pdf_path
    )


    return {
        "original": original_path,
        "image": processed_path,
        "pdf": pdf_path,
        "detected": (
            document_points is not None
        )
    }


if __name__ == "__main__":

    import sys


    if len(sys.argv) != 2:

        print("Usage:")
        print(
            "python scanner.py image.jpg"
        )

        sys.exit(1)


    input_image = sys.argv[1]


    print(
        f"Processing: {input_image}"
    )


    try:

        result = scan_document(
            input_image
        )


        print()
        print("Scan complete.")

        print(
            f"Document detected: "
            f"{result['detected']}"
        )

        print(
            f"Image: {result['image']}"
        )

        print(
            f"PDF: {result['pdf']}"
        )


    except Exception as error:

        print(
            f"ERROR: {error}"
        )
