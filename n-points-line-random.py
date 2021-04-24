
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

def intersect_origin_line(points, radius):
    """
    Checks whether any points come within radius of origin line

    Args:
      points: full list of points 
      radius: radius of each point

    Returns:
      True if one or more points intersect origin line, False otherwise
    """
    for p in points:
        if p[1] < radius:
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
    num_stacks = (arena_size - 3*radius) // radius
    num_per_stack = num_points // num_stacks

    axes.cla()
    plt.title(f"Best config for {num_per_stack} layers\n Avg. Distance = {power:.3f}")
    maxvalx = max([x[0] for x in best_points]) + 3 * radius
    maxvaly = max([x[1] for x in best_points]) + 3 * radius
    plt.xlim(-arena_size-radius, maxvalx)
    plt.ylim(0, maxvaly)
    for p in best_points:
        axes.add_patch(plt.Circle(p, radius))
        plt.plot([p[0], p[2]], [p[1], p[3]], "b")
    plt.pause(0.05)

def in_violation(points, radius, arena_size):
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
    
    if intersect_origin_line(points, radius):
        return True
    
    return False

def main(args):
    if len(args) > 2:
        num_points = int(args[1])
        num_trials = int(args[2])
        dynamics(num_points, num_trials)
    elif len(args) > 1:
        num_points = int(args[1])
        dynamics(num_points)
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
        if p1[1] < p2[1]:   # behind doesn't block
            continue
        if closest_distance_to_line(m,b,p2[0],p2[1]) < radius:
            return True
    return False

        
def assign_foci(points, radius, arena_size, max_x, min_x):
    """
    Adjusts foci of all points if possible without blocking, maximizing to closest focus, otherwise
    just returns input points

    Args:
         points: list of points to adjust
         radius: radius of each point

    Returns: 
        success flag, new points
        If foci could be adjusted successfully, flag is True, otherwise False.
    """

    can_adjust = True
    new_points = points.copy()
    for i,p in enumerate(points):
        can_adjust = False
        for d in range(arena_size): # scan x-axis in order of closest distance to point
            for side in [1, -1]: # both left and right
                displacement = side * d
                x = new_points[i][0] + side * d
                if x > max_x or x < min_x:
                    continue
                new_p = (new_points[i][0], new_points[i][1], x, 0)
                new_points[i] = new_p
                if not is_blocked(new_p, new_points, radius):
                    can_adjust = True
                    break
            if can_adjust:
                break
        if not can_adjust:
            return False, points
                    
    return can_adjust, new_points


def random_init(num_points, arena_size, radius):
    """
    Randomly initializes locations of points in an arena in positive-y plane. Points will not touch y=0 axis within their radius.

    Args:
      num_points: number of points to initialize
      arena_size: distance to either size of x=0 axis, and above y=0 axis
      radius: size of point

    Returns:
      List of initialized points
    """
    points = []
    y_max = 5 * 2 * radius * num_points
    for j in range(num_points):
        points.append((random.randint(-arena_size+radius,arena_size-radius), random.randint(radius,y_max), random.randint(-arena_size,arena_size), 0))
    return points


def layered_init(num_points, arena_size, radius):
    """
    Randomly initializes x-locations of points, one in each stepped y-layer in an arena in positive-y plane. Points will not touch y=0 axis within their radius.

    Args:
      num_points: number of points to initialize
      arena_size: distance to either size of x=0 axis, and above y=0 axis
      radius: size of point

    Returns:
      List of initialized points
    """
    scale = 1.0
    points = []
    for n in range(num_points):
        points.append((random.randint(-arena_size + radius, arena_size - radius), scale * (n + 1) * 2 * radius, 0, 0))
        scale *= 1.1
    return points


def double_side_init(num_points, arena_size, radius):
    """
    Places points along sides exponentially spaced

    Args:
      num_points: number of points to initialize
      arena_size: distance to either size of x=0 axis, and above y=0 axis
      radius: size of point

    Returns:
      List of initialized points
    """
    points = []
    separation = 2.5 * radius
    scaler = 1.1
    curr_y = 0
    for n in range(num_points//2):
        curr_y += separation 
        points.append((-arena_size + radius, curr_y, 0, 0))
        points.append((arena_size - radius, curr_y, 0, 0))
        separation *= scaler
    if len(points) < num_points: # handles odd number of points
        curr_y += separation 
        points.append((-arena_size + radius, curr_y, 0, 0))
    return points
    


def stacks_init(num_points, arena_size, radius):
    """
    Places points in multiple stacks

    Args:
      num_points: number of points to initialize
      arena_size: distance to either size of x=0 axis, and above y=0 axis
      radius: size of point

    Returns:
      List of initialized points
    """
    points = []
    orig_separation = 2 * radius
    scaler = 2
    curr_y = 0
    num_stacks = (arena_size - 3*radius) // radius
    num_per_stack = num_points // num_stacks
    x_per_stack = 2 * arena_size / num_stacks 
    for n in range(num_stacks):
        curr_x = -arena_size + radius + n * x_per_stack
        curr_y = 0
        separation = orig_separation
        for i in range(num_per_stack): 
            curr_y += separation 
            points.append((curr_x, curr_y, curr_x + x_per_stack - radius + 5, 0))
            separation *= scaler
    
    return points

def angled_init(num_points, arena_size, radius):
    """
    Places points in multiple angled stacks

    Args:
      num_points: number of points to initialize
      arena_size: distance to either size of x=0 axis, and above y=0 axis
      radius: size of point

    Returns:
      List of initialized points
    """
    points = []
    num_stacks = (arena_size - 3*radius) // radius
    num_per_stack = num_points // num_stacks
    x_per_stack =  random.randint(2 * radius, num_per_stack * radius)    # heuristic

    angle = 0
    curr_x = 0
    curr_y= radius
    for i in range(num_per_stack):
        for n in range(num_stacks):
            x_shift = -arena_size + radius + n * x_per_stack  
            points.append((curr_x + x_shift, curr_y, x_shift + x_per_stack - radius + 5, 0))
        angle = angle + random.random() * (3.14159 / 2 - angle) 

        # For smoother curving queues, the following is faster but perhaps not as accurate
        #        angle = angle + random.random() * (3.14159 / 2 - angle) / (num_per_stack - i)
        curr_x = curr_x + 2*radius * (math.sin(angle))
        curr_y = curr_y + 2*radius * (math.cos(angle))

    return points



def dynamics(num_points=20, num_trials=200):
    """
    In this model each point has its own 'focus point' on the line.
    This focus point is updated if another circle blocks LOS

    Args:
      num_points: number of points to test, divided into 5 stacks 
      num_trials: number of trials to test (each having several million random positions)
     
    Returns:
      nothing
    """
    
    radius = 100
    arena_size = radius * 8
    num_steps = 6000
    best_power = -10000
    best_points = []
    figure, axes = plt.subplots()
    axes.set_aspect( 1 )
    best_avg_distance = 1000

    for trialnum in range(num_trials):

        # first find a legal starting position in area bounded below by y=0
        for step in range(num_steps * num_steps):
            points = angled_init(num_points, arena_size, radius)
            
            # simple check whether circles overlap
            if in_violation(points, radius, arena_size):
                continue

            spacing = points[1][0] - points[0][0]
            max_x = max([x[0] for x in points if x[1]==radius]) + spacing - radius
            min_x = min([x[0] for x in points if x[1]==radius]) + radius
            success, points = assign_foci(points, radius, arena_size, max_x, min_x)
            if success:
                break

        # enforce periodicity
        num_stacks = (arena_size - 3*radius) // radius
        num_per_stack = num_points // num_stacks
        for i in range(num_per_stack):
            this_idx = (i + 1) * num_stacks - 1
            prev_point = points[this_idx - 1]
            points[this_idx] = (prev_point[0] + spacing, prev_point[1], prev_point[2] + spacing, prev_point[3])
            
        distances = [ math.sqrt((x[0]-x[2])**2 + (x[1]-x[3])**2)/radius for x in points]
        avg_distance = sum(distances)/len(distances)
        power = 1/avg_distance - (max_x - min_x)/2/radius

        if power  >  best_power:
            best_power = power
            best_avg_distance = avg_distance
            best_points = points
            print(f"Best power = {best_power}, distance = {best_avg_distance}")
            plotcircles_to_foci(figure, axes, best_points, radius, arena_size, num_points, step + 1, avg_distance)

        print(f"Trial#: {trialnum}")
        
    plotcircles_to_foci(figure, axes, best_points, radius, arena_size, num_points, trialnum+1, best_avg_distance)
    plt.show()
    

      
if __name__ == '__main__':
    main(sys.argv)
n-points-line-random.py
Displaying n-points-line-random.py
