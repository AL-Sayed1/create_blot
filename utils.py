import svgpathtools
import numpy as np
from xml.dom import minidom
import re
from io import BytesIO, StringIO
from PIL import Image
import cv2


def parse_transform(transform_str):
    if not transform_str:
        return 1, 1, 0, 0

    scale_x = scale_y = 1
    translate_x = translate_y = 0

    if "scale" in transform_str:
        scale = re.findall(r"scale\((.*?)\)", transform_str)
        if scale:
            values = [float(x) for x in scale[0].split(",")]
            scale_x = values[0]
            scale_y = values[-1] if len(values) > 1 else values[0]

    if "translate" in transform_str:
        translate = re.findall(r"translate\((.*?)\)", transform_str)
        if translate:
            values = [float(x) for x in translate[0].split(",")]
            translate_x = values[0]
            translate_y = values[1] if len(values) > 1 else 0

    return scale_x, scale_y, translate_x, translate_y


def get_svg_dimensions(svg_elem):
    viewBox = svg_elem.getAttribute("viewBox")
    if viewBox:
        _, _, width, height = map(float, viewBox.split())
        return width, height

    width = svg_elem.getAttribute("width")
    height = svg_elem.getAttribute("height")

    for unit in ["px", "pt", "mm", "cm", "in"]:
        width = str(width).replace(unit, "")
        height = str(height).replace(unit, "")

    return float(width), float(height)


def get_path_complexity(path):
    return len(path) * len(path.continuous_subpaths())


class ConvertToBlot:
    def __init__(self, file, file_type):
        """
        Args:
            file: BytesIO or bytes object containing SVG or PNG data from Streamlit upload
            file_type: str, either 'svg' or 'png'
        """
        self.file_type = file_type
        self.file_content = file.read() if hasattr(file, "read") else file

        if self.file_type == "svg":
            self.polylines = self._svg_to_blot()
        elif self.file_type == "png":
            self.polylines = self._png_to_blot()
        else:
            raise ValueError("Unsupported file type. Use 'svg' or 'png'.")

        self.blot_js = self.blot_code()

    def _png_to_blot(self):
        """Initialize polylines from PNG file content"""
        image = Image.open(BytesIO(self.file_content)).convert(
            "L"
        )
        image = image.point(
            lambda p: p < 128 and 255
        )
        image = image.convert("1")

        image = image.transpose(Image.FLIP_TOP_BOTTOM)

        open_cv_image = np.array(image, dtype=np.uint8)

        contours, hierarchy = cv2.findContours(
            open_cv_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )

        polylines = []
        for contour in contours:
            polyline = contour.reshape(-1, 2).tolist()
            polylines.append(polyline)

        return polylines

    def _svg_to_blot(self):
        """Initialize polylines from SVG file content"""
        svg = minidom.parseString(self.file_content)
        paths = svg.getElementsByTagName("path")
        polylines = []

        for path in paths:
            d = path.getAttribute("d")
            path_obj = svgpathtools.parse_path(d)
            polyline = []

            for segment in path_obj:
                num_samples = 200
                for i in range(num_samples + 1):
                    point = segment.point(i / num_samples)
                    polyline.append([point.real, -point.imag])

            polylines.append(polyline)

        return polylines

    def blot_code(self):
        blot_js = f"""let polylines = {self.polylines};

// Optimize polylines
polylines = bt.resample(polylines, 0.5); // Resample with 0.5mm spacing
polylines = bt.simplify(polylines, 0.1, true); // High quality simplification

// Calculate optimal scale to fit workarea
const bbox = bt.bounds(polylines);
const maxDim = Math.max(bbox.width, bbox.height);
const scaleFactor = Math.min(125/maxDim, 1) * 0.95; // 95% of max size

bt.scale(polylines, scaleFactor);
bt.originate(polylines) 
drawLines(polylines);
    """
        return blot_js
