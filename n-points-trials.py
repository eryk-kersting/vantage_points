
#!/usr/bin/python


import matplotlib.pyplot as plt
import random
import math
import sys


def closest_distance_to_line(m,b,x,y):
    """
    Returns closest distance between point (x,y) and line y=mx+b

    Args:
      m: slope of the line
      b: intercept of the line
      x: x-coord of the point
      y: y-coord of the point

    Returns:
      closest distance between the point and the line.
    """
    linex = (-b + y + x/m)/(m + 1/m)
    liney = m * linex + b
    distance = math.sqrt((x - linex)**2 + (y - liney)**2)
    return distance

def self_intersect(points, radius):
    """
    Checks whether circles intersect eachother

    Args:
      points: full list of points 
      radius: radius of each point

    Returns:
      True if one or more points intersect, False otherwise
    """
    num_points = len(points)
    for i in range(num_points):
        for j in range(i + 1, num_points):
            p1 = points[i]
            p2 = points[j]
            if (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 < 4*radius**2:
                return True
    return False


def intersect_origin(points, radius):
    """
    Checks whether any points come within radius of origin

    Args:
      points: full list of points 
      radius: radius of each point

    Returns:
      True if one or more points intersect origin, False otherwise
    """
    for p in points:
        if (p[0]**2 + p[1]**2 < radius**2):
            return True
    return False

def plotcircles_to_foci(figure, axes, best_points, radius, arena_size, num_points, num_steps, power):
    """
    Plots circles as well as lines from centers to foci

    Args:
      figure: figure object to draw
      axes: axes object
      best_points: points to plot
      radius: radius of each circle
      arena_size: plot area
      num_points: number of total points
      num_steps: number of steps at this iteration
      power: power corresponding to this configuration of points

    Returns:
      nothing
    """
    axes.cla()
    plt.title(f"Best config for n={num_points} \n Power = {power:.3f}" )
    plt.xlim(-arena_size, arena_size)
    plt.ylim(-arena_size, arena_size)
    for p in best_points:
        axes.add_patch(plt.Circle(p, radius))
        plt.plot([p[0], p[2]], [p[1], p[3]], "b")
    plt.pause(0.05)


def in_violation_full(points, radius, arena_size):
    """
    Performs various checks to see whether points physically acceptable, e.g. do they overlap or cross arena boundaries

    
    Args:
      points: full list of points 
      radius: radius of each point
      arena_size: maximum absolute x-value

    Returns:
      True if one or more points in violation, False otherwise
    """
    degenerate = False
    num_points = len(points)
    for i in range(num_points):
        for j in range(i + 1, num_points):
            p1 = points[i]
            p2 = points[j]
            if p1[0] == p2[0] and p1[1] == p2[1]:
                degenerate = True
    if degenerate:
        return True
    
    if self_intersect(points, radius):
        return True
    
    if intersect_origin(points, radius):
        return True

    for p in points:
        if is_blocked(p, points, radius):
            return True
    
    return False

def sum_forces(i, points, repulse, repulse_d, radius):
    """
    Computes forces on the i-th point, both attractive from its focus line, and repulsive via contact with other points.

    Args:
      i: index of the point to compute
      points: full collection of points
      repulse: multiplier for repulsive force
      repulse_d: distance (in units of radius) over which repulsive force exists
      radius: size of point

    Returns:
      x- and y- components of the force on the input point
    """
    distance_to_focus = math.sqrt((points[i][0] - points[i][2])**2 + (points[i][1] - points[i][3])**2)
    central_force = ((points[i][2] - points[i][0])/distance_to_focus, (points[i][3] - points[i][1])/distance_to_focus)  # constant force to focus
    r_force = (0,0) 
    for j,p in enumerate(points):
        if i == j:
            continue
        distance = math.sqrt((points[i][0] - p[0])**2 + (points[i][1] - p[1])**2)
        if abs(distance) < repulse_d * abs(radius):
            r_force = (r_force[0] + repulse * (points[i][0] - p[0])/radius, r_force[1] + repulse * (points[i][1] - p[1])/radius)

    f_x = central_force[0] + r_force[0]
    f_y = central_force[1] + r_force[1]    
    return f_x, f_y


def main(args):
    if len(args) > 3:
        num_points = int(args[1])
        repulse = float(args[2])
        repulse_d = float(args[3])
        dynamics(num_points, repulse, repulse_d)
    else:
        dynamics()


def is_blocked(p1, points, radius):
    """                                                                                            
    Tests whether point's LOS to its focus is blocked by other points

    
    Args:
      p1: point to check
      points: full list of points 
      radius: radius of each point

    Returns:
      True if one or more points block the input point's LOS, False otherwise
    """
    # first find line to focus
    m = (p1[1] - p1[3] + 0.01)/(p1[0] - p1[2] + 0.01)
    b = p1[1] - m * p1[0]

    for p2 in points:
        if p2 == p1:
            continue
        if (p1[1]**2 + p1[0]**2) < (p2[0]**2 + p2[1]**2) or (p1[0]*p2[0]<0 and p1[1]*p2[1]<0):   # behind doesn't block
            continue
        if closest_distance_to_line(m,b,p2[0],p2[1]) < radius:
            return True
    return False


def random_init_uniform(num_points, arena_size, radius):
    points = []
    for j in range(num_points):
        points.append((random.randint(-arena_size, arena_size), random.randint(-arena_size, arena_size), 0,0))
    return points


def dynamics(num_points=4, repulse=50, repulse_d=2.1):
    """
    In this model each point has its own 'focus point' on the line which it
    is attracted to; this focus point is updated if another circle blocks LOS
    The inverse-square distance to each viewer is optimized over trials.

    Args:
      num_points: number of points to test
      repulse: multiplier for repulsive force (relative to attractive focus force)
      repulse_d: distance (in units of radius) over which repulsive force exists    

    Returns:
      nothing
    """
    
    radius = 200
    arena_size = 2*radius * num_points 
    num_steps = 10000
    figure, axes = plt.subplots()
    axes.set_aspect( 1 )
    max_arena =  (1 + radius + arena_size)  # for a better picture
    vmax_arena = max_arena
    numtrials = 100
    very_best_power = 0
    very_best_points = []
    orig_repulse = repulse
    orig_repulse_d = repulse_d
    
    for trialnum in range(numtrials):
    
        best_power = 0
        best_points = []
        repulse = orig_repulse
        repulse_d = orig_repulse_d

        # first find a legal starting position in area bounded below by y=0
        for step in range(num_steps * num_steps):
            points = random_init_uniform(num_points, arena_size, radius)

            # simple check whether circles overlap
            if in_violation_full(points, radius, arena_size):
                continue
            else:
                break

        for step in range(num_steps):
            magnitude = max(1, radius - 10 * (step/100))  # number of grid points to move each time
            repulse_d = max(0, repulse_d - 0.1*step//1000)
            repulse = max(0, repulse - 0.5 * step//1000)

            
            # calculate force on each point and move if not in violation
            new_points = points.copy()
            no_change = True
            for i,p in enumerate(points):
                f_x, f_y  = sum_forces(i, points, repulse, repulse_d, radius)
                norm = math.sqrt(f_x**2 + f_y**2)
                p_delta_x = magnitude * f_x / norm
                p_delta_y = magnitude * f_y / norm
                new_points[i] = (p[0] + p_delta_x, p[1] + p_delta_y, p[2], p[3])
                if in_violation_full(new_points, radius, arena_size):
                    new_points[i] = p  # rollback the motion
                    continue
                else:
                    no_change = False

            points = new_points.copy()

            inv_sq_distances = [radius * radius * ((x[0]-x[2])**2 + (x[1]-x[3])**2)**(-1) for x in points]
            power = sum(inv_sq_distances)
            if power > best_power:
                best_power = power
                best_points = points
                max_arena = radius + max([math.sqrt(x[0]**2 + x[1]**2) for x in points])

        print(trialnum, best_power, best_points)
        if best_power > very_best_power:
            very_best_power = best_power
            very_best_points = best_points
            vmax_arena = max_arena

    plotcircles_to_foci(figure, axes, very_best_points, radius, vmax_arena, num_points, trialnum, very_best_power)
    plt.show()
    

   
    
if __name__ == '__main__':
    main(sys.argv)

