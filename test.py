from PIL import Image

def png_to_blot(uploaded_file):
    image = Image.open(uploaded_file).convert('RGBA')
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

    print(width)
    print(height)

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