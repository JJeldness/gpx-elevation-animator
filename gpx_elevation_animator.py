import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import gpxpy
import gpxpy.gpx
import sys
import argparse

from math import sin, cos, sqrt, atan2, radians
from scipy import interpolate
from scipy.ndimage.filters import gaussian_filter1d
from matplotlib.ticker import FuncFormatter

def calculate_distance(a, b):
    # approximate radius of earth in km
    R = 6371000.0

    lat1 = radians(a[0])
    lon1 = radians(a[1])
    lat2 = radians(b[0])
    lon2 = radians(b[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def create_plot(args):
    gpx_file = open(args.gpx_file, 'r')
    gpx = gpxpy.parse(gpx_file)

    fig, ax = plt.subplots(figsize=(args.length/args.dpi, args.height/args.dpi), dpi=args.dpi)
    plt.tight_layout()
    plt.gcf().subplots_adjust(bottom=0.2, left=0.1)
    # fig.suptitle('Wysokość', fontsize=16)
    # ax.get_xaxis().set_visible(False)
    ax.set_ylabel('Wysokość [m n.p.m.]')
    ax.set_xlabel('Dystans [km]')
    ax.margins(0, 0)
    ax.grid(True)

    points = gpx.tracks[0].segments[0].points
    points = list(filter(lambda p: p.elevation, points))

    x = [0.0]

    for i in range(1, len(points)):
        prev = points[i-1]
        curr = points[i]
        distance = calculate_distance((prev.latitude, prev.longitude), (curr.latitude, curr.longitude)) / 1000.0
        x.append(x[i-1] + distance)

    t = list(map(lambda p: p.time.timestamp(), points))
    t = list(map(lambda x: (x-t[0])/args.speedup*args.fps, t))

    y = list(map(lambda p: p.elevation, points))
    y = gaussian_filter1d(y, sigma=args.smoothness)
    f = interpolate.interp1d(t, x)

    line, = ax.plot(x, y, color=args.color)
    current_moment = ax.axvline(x=0, color=args.color)
    ymin = min(y)
    ymax = max(y)
    margin_value = (ymax - ymin) * args.margin
    ax.axis([None, None, ymin - margin_value, ymax + margin_value])

    def animate(i):
        current_moment.set_xdata(f(i))
        ax.collections.clear()
        p = plt.fill_between(x, y, 0, where=x<f(i), facecolor = args.color, alpha = 0.2)
        return current_moment, p

    ani = animation.FuncAnimation(
        fig, animate, interval=1000/args.fps, blit=True, frames=int(t[-1]+1), repeat = False)

    if (args.output):
        from matplotlib.animation import FFMpegWriter
        writer = FFMpegWriter(fps=args.fps, metadata=dict(artist='Fundacja Beskid'), bitrate=args.bitrate)
        ani.save(args.output[1:-1], writer=writer)
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Elevation animation based on gpx data. Compatibile with GpxAnimator.')

    parser.add_argument('gpx_file', type=str, help='Path to gpx file')
    parser.add_argument('--fps', dest='fps', type=int, default=24, help='Output framerate. Defaults to 24')
    parser.add_argument('--speedup', dest='speedup', type=int, default=100, help='Speedup of animation. Defaults to 100')
    parser.add_argument('--output', '-o', dest='output', type=str, help='Output file. If not specified animation will be displayed')
    parser.add_argument('--margin', dest='margin', type=float, default=0.05, help='Top margin of plot. Defaults to 0.05')
    parser.add_argument('--length', dest='length', type=int, default=800 ,help='Figure length (in pixels). Defaults to 800')
    parser.add_argument('--height', dest='height', type=int, default=300, help='Figure height (in pixels). Defaults to 300')
    parser.add_argument('--smooth', dest='smoothness', type=int, default=20, help='How much to smooth the plot. Defaults to 20')
    parser.add_argument('--color', '-c', dest='color', type=str, default='#7DA417', help='Color of plot e.g. #AABBCC. Defaults to #7DA417')
    parser.add_argument('--dpi', dest='dpi', type=int, default=100, help='Output dpi. Defaults to 100')
    parser.add_argument('--bitrate', dest='bitrate', type=int, default=1800, help='Output bitrate. Defaults to 1800')

    args = parser.parse_args()

    create_plot(args)


if __name__ == "__main__":
    main()
