import svgpathtools
import numpy as np
from xml.dom import minidom
import re


def px_to_mm(px):
    return px * 0.2645833333


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
        return px_to_mm(width), px_to_mm(height)

    width = svg_elem.getAttribute("width")
    height = svg_elem.getAttribute("height")

    for unit in ["px", "pt", "mm", "cm", "in"]:
        width = str(width).replace(unit, "")
        height = str(height).replace(unit, "")

    return px_to_mm(float(width)), px_to_mm(float(height))


def get_path_complexity(path):
    return len(path) * len(path.continuous_subpaths())


from io import StringIO, BytesIO


class SVGToBlot:
    def __init__(self, svg_file):
        """
        Args:
            svg_file: BytesIO or bytes object containing SVG data from Streamlit upload
        """
        self.svg_content = svg_file.read() if hasattr(svg_file, "read") else svg_file
        self.polylines = self._generate_polylines()
        self.blot_js = self.svg_to_blot()

    def _generate_polylines(self):
        """Initialize polylines from SVG file content"""
        try:
            svg_string = (
                self.svg_content.decode("utf-8")
                if isinstance(self.svg_content, bytes)
                else self.svg_content
            )

            svg_file = StringIO(svg_string)
            paths, attributes = svgpathtools.svg2paths(svg_file)

            doc = minidom.parseString(svg_string)
            svg_elem = doc.getElementsByTagName("svg")[0]
            self.width, self.height = get_svg_dimensions(svg_elem)

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
                            x = px_to_mm((point.real * scale_x + tx))
                            y = self.height - px_to_mm((point.imag * scale_y + ty))
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

    def svg_to_blot(self):
        blot_js = f"""const {{ scale, translate, originate, resample, simplify, bounds }} = blotToolkit;
    
    // Initialize document dimensions
    setDocDimensions({self.width}, {self.height});
    
    let polylines = {self.polylines};
    
    // Optimize polylines
    polylines = resample(polylines, 0.5); // Resample with 0.5mm spacing
    polylines = simplify(polylines, 0.1, true); // High quality simplification
    
    // Calculate optimal scale to fit workarea
    const bbox = bounds(polylines);
    const maxDim = Math.max(bbox.width, bbox.height);
    const scaleFactor = Math.min(125/maxDim, 1) * 0.95; // 95% of max size
    
    scale(polylines, scaleFactor);
    
    drawLines(polylines);
    """
        return blot_js
