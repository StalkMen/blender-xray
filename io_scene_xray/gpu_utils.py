import math

import gpu
from gpu_extras.batch import batch_for_shader


def gen_arc(radius, start, end, num_segments, fconsumer, indices, close=False):
    theta = (end - start) / num_segments
    cos_th, sin_th = math.cos(theta), math.sin(theta)
    x, y = radius * math.cos(start), radius * math.sin(start)
    if indices:
        start_index = indices[-1][-1] + 1
    else:
        start_index = 0
    index = 0
    for _ in range(num_segments):
        fconsumer(x, y)
        indices.append(
            (start_index + index, start_index + index + 1)
        )
        index += 1
        _ = x
        x = x * cos_th - y * sin_th
        y = _ * sin_th + y * cos_th
    if close:
        fconsumer(x, y)


def gen_circle(radius, num_segments, fconsumer, indices):
    gen_arc(radius, 0, 2.0 * math.pi, num_segments, fconsumer, indices, close=True)


def draw_wire_cube(hsx, hsy, hsz, color):
    coords = (
        (-hsx, -hsy, -hsz),
        (+hsx, -hsy, -hsz),
        (+hsx, +hsy, -hsz),
        (-hsx, +hsy, -hsz),

        (-hsx, -hsy, +hsz),
        (+hsx, -hsy, +hsz),
        (+hsx, +hsy, +hsz),
        (-hsx, +hsy, +hsz),
    )
    indices = (
        (0, 1), (1, 2),
        (2, 3), (3, 7),
        (2, 6), (1, 5),
        (0, 4), (4, 5),
        (5, 6), (6, 7),
        (4, 7), (0, 3)
    )
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_wire_sphere(radius, num_segments, color):
    coords = []
    indices = []
    gen_circle(radius, num_segments, lambda x, y: coords.append((x, y, 0)), indices)
    gen_circle(radius, num_segments, lambda x, y: coords.append((0, x, y)), indices)
    gen_circle(radius, num_segments, lambda x, y: coords.append((y, 0, x)), indices)

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_wire_cylinder(radius, half_height, num_segments, color):
    coords = []
    indices = []
    gen_circle(radius, num_segments, lambda x, y: coords.append((x, -half_height, y)), indices)
    gen_circle(radius, num_segments, lambda x, y: coords.append((x, +half_height, y)), indices)
    coords.extend([
        (-radius, -half_height, 0),
        (-radius, +half_height, 0),
        (+radius, -half_height, 0),
        (+radius, +half_height, 0),
        (0, -half_height, -radius),
        (0, +half_height, -radius),
        (0, -half_height, +radius),
        (0, +half_height, +radius)
    ])
    start_index = indices[-1][-1] + 1
    for i in range(start_index, start_index + 8, 2):
        indices.extend((
            (i, i + 1),
            (i +1, i)
        ))

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_cross(size, color):
    coords = (
        (-size, 0, 0),
        (+size, 0, 0),
        (0, -size, 0),
        (0, +size, 0),
        (0, 0, -size),
        (0, 0, +size)
    )
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def gen_limit_circle(rotate, radius, num_segments, axis, color, min_limit, max_limit):
    def gen_arc_vary(radius, start, end, indices):
        num_segs = math.ceil(num_segments * abs(end - start) / (math.pi * 2.0))
        if num_segs:
            gen_arc(radius, start, end, num_segs, fconsumer, indices, close=True)

    grey_color = (0.5, 0.5, 0.5, 0.8)
    coords = []
    indices = []
    draw_functions = {
        'X': (lambda x, y: coords.append((0, -x, y))),
        'Y': (lambda x, y: coords.append((-y, 0, x))),
        'Z': (lambda x, y: coords.append((-x, -y, 0)))
    }
    fconsumer = draw_functions[axis]

    gen_arc_vary(radius, min_limit, max_limit, indices)
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords, }, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

    coords = []
    indices = []
    gen_arc_vary(radius, max_limit, 2.0 * math.pi + min_limit, indices)
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords, }, indices=indices)
    shader.bind()
    shader.uniform_float("color", grey_color)
    batch.draw(shader)

    coords = []
    indices = []
    gen_arc(radius, rotate, rotate + 1, 1, fconsumer, indices, close=False)

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'POINTS', {"pos": coords, })
    shader.bind()
    shader.uniform_float("color", (1.0, 1.0, 0.0, 1.0))
    batch.draw(shader)


def draw_joint_limits(rotate, min_limit, max_limit, axis, radius):
    colors = {
        'X': (1.0, 0.0, 0.0, 1.0),
        'Y': (0.0, 1.0, 0.0, 1.0),
        'Z': (0.0, 0.0, 1.0, 1.0)
    }

    color = colors[axis]
    gen_limit_circle(
        rotate, radius, 24, axis, color,
        min_limit, max_limit
    )
