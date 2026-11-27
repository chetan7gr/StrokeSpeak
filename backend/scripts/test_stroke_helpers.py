import json

def line_pts(p0, p1, n=16):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = round(p0[0] + (p1[0] - p0[0]) * t, 6)
        y = round(p0[1] + (p1[1] - p0[1]) * t, 6)
        pts.append({"x": x, "y": y, "time": i * 10})
    return pts

def quad_pts(p0, p1, p2, n=20):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1.0 - t
        x = round(u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0], 6)
        y = round(u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1], 6)
        pts.append({"x": x, "y": y, "time": i * 10})
    return pts

def pts_to_svg_d(pts):
    if not pts: return ""
    d = f"M {pts[0]['x']*100:.1f} {pts[0]['y']*100:.1f}"
    for p in pts[1:]:
        d += f" L {p['x']*100:.1f} {p['y']*100:.1f}"
    return d

print("Helper functions defined successfully")
