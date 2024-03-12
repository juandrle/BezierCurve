from rendering import Scene, RenderWindow

def deboor(j, i, degree, controlpoints, knotvector, t):
    if j == 0:
        return controlpoints[i]
    temp = knotvector[i]
    numerator = (t - temp)
    denominator = (knotvector[i - j + degree] - temp)
    # blending coefficient : alpha
    # if the denominator is close to 0 -> alpha 0
    if abs(denominator) < 1e-6:
        alpha = 0
    else:
        alpha = numerator / denominator
    left = deboor(j-1, i-1, degree, controlpoints, knotvector, t)
    right = deboor(j-1, i, degree, controlpoints, knotvector, t)
    # weighted interpolation of all points from the zip operation
    point = [(l * (1 - alpha)) + (r * alpha) for l, r in zip(left, right)]
    return point
    

def bezier_curve_points(order, controlpoints, knotvector, numPoints):
    points = []
    # curve iteration to add points
    for i in range(numPoints + 1):
        t = (float(i) / numPoints) * knotvector[-1]
        r = 0
        for j in range(len(knotvector)):
            if t == max(knotvector):
                r = len(knotvector) - order - 1
                break
            if knotvector[j] > t:
                r = j - 1
                break
        point = deboor(order - 1, r, order, controlpoints, knotvector, t)
        points.append((point[0], point[1]))
    return points
    



# call main
if __name__ == '__main__':
    print("bezierTemplate.py")
    print("pressing 'C' should clear the everything")

    # set size of render viewport
    width, height = 640, 480

    # instantiate a scene
    scene = Scene(width, height, bezier_curve_points, "Bezier Curve Template")

    rw = RenderWindow(scene)
    rw.run()
 