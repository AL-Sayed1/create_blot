import svgpathtools
import numpy as np
from xml.dom import minidom
import re
from io import BytesIO, StringIO
from PIL import Image


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

        if self.file_type == 'svg':
            self.polylines = self._svg_to_blot()
        elif self.file_type == 'png':
            self.polylines = self._png_to_blot()
        else:
            raise ValueError("Unsupported file type. Use 'svg' or 'png'.")

        self.blot_js = self.blot_code()

    def _svg_to_blot(self):
        """Initialize polylines from SVG file content"""
        try:
            svg_string = (
                self.file_content.decode("utf-8")
                if isinstance(self.file_content, bytes)
                else self.file_content
            )

            svg_file = StringIO(svg_string)
            paths, attributes = svgpathtools.svg2paths(svg_file)

            doc = minidom.parseString(svg_string)
            svg_elem = doc.getElementsByTagName("svg")[0]

            all_polylines = []
            for path, attr in zip(paths, attributes):
                transform = attr.get("transform", "")
                scale_x, scale_y, tx, ty = parse_transform(transform)

                complexity = get_path_complexity(path)
                base_samples = 100
                max_samples = 1000
                samples = min(max(base_samples, complexity * 5), max_samples)

                points = []
                for subpath in path.continuous_subpaths():
                    subpath_points = []
                    for t in np.linspace(0, 1, samples):
                        try:
                            point = subpath.point(t)
                            x = (point.real * scale_x + tx)
                            y = self.height - (point.imag * scale_y + ty)
                            subpath_points.append([x, y])
                        except:
                            continue
                    if subpath_points:
                        points.append(subpath_points)

                for subpath_points in points:
                    points_str = ",".join(f"[{x},{y}]" for x, y in subpath_points)
                    all_polylines.append(f"[{points_str}]")

            return f"[{','.join(all_polylines)}]"

        except Exception as e:
            raise ValueError(f"Failed to process SVG: {str(e)}")
        
    def _png_to_blot(self):
        """Initialize polylines from PNG file content"""
        image = Image.open(BytesIO(self.file_content)).convert('RGBA')
        threshold = 128
        im_row_list = []
        for y in range(image.height):
            row = ''
            for x in range(image.width):
                r, g, b, a = image.getpixel((x, y))
                brightness = (r + g + b) / 3
                if a == 0 or brightness > threshold:
                    row += '1'
                else:
                    row += '0'
            im_row_list.append(row)
    
        width = image.width
        height = image.height

        lines = []
    
        def makeLine(startX, endX, y):
            y = height - y
            lines.append([
                [startX, y],
                [endX, y]
            ])
    
        for y in range(height):
            line_beginning = -1
    
            for x in range(width):
                if im_row_list[y][x] == '0':
                    if line_beginning == -1:
                        line_beginning = x
                else:
                    if line_beginning != -1:
                        makeLine(line_beginning, x, y)
                        line_beginning = -1
    
            if line_beginning != -1:
                makeLine(line_beginning, width, y)
    
        return lines

        
    def blot_code(self):
        blot_js = f"""const {{ scale, translate, originate, resample, simplify, bounds }} = blotToolkit;

let polylines = {self.polylines};

// Optimize polylines
polylines = resample(polylines, 0.5); // Resample with 0.5mm spacing
polylines = simplify(polylines, 0.1, true); // High quality simplification

// Calculate optimal scale to fit workarea
const bbox = bounds(polylines);
const maxDim = Math.max(bbox.width, bbox.height);
const scaleFactor = Math.min(125/maxDim, 1) * 0.95; // 95% of max size

scale(polylines, scaleFactor);
bt.originate(polylines) 
drawLines(polylines);
    """
        return blot_js