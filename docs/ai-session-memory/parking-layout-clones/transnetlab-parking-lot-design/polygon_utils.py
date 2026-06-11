import geopandas as gpd
import osmnx as ox
from shapely import wkt
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.affinity import rotate
import math
import numpy
import matplotlib.pyplot as plt
import csv
import itertools
import os
import config
import warnings
from pyproj import Geod

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
purple = {'r': 126 / 255, 'g': 71 / 255, 'b': 148 / 255}
red = {'r': 141 / 255, 'g': 55 / 255, 'b': 51 / 255}


def get_parking_polygon_by_index(index, csv_file):
    """Generate a parking lot polygon from the csv file.

    Parameters:
        index (int): index of the parking lot polygon in the csv file
        csv_file (str): path to the csv file

    Returns:
        polygon (Polygon): the parking lot polygon
    """
    polygon_data_string = None
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader)  # skip the header row

        # Find the index of the desired header
        column_polygon = header.index('the_geom')
        column_index = header.index('SOURCE_ID')
        column_area = header.index('SHAPE_Area')
        for row in csv_reader:
            if int(row[column_index]) == index:  # access the values in each row
                polygon_data_string = row[column_polygon]
                area = row[column_area]
                break

    if polygon_data_string is None:
        raise ValueError("The parking lot index is not in records.")

    # Load the polygon geometry from the string
    geom = wkt.loads(polygon_data_string)

    # Create a GeoDataFrame with the polygon geometry
    polygon = gpd.GeoDataFrame(geometry=[geom], crs='EPSG:4326')

    return polygon, area  # .geometry.iloc[0]


def extract_parking_polygons_from_OSM(coordinates):
    """Extract parking polygons from OSM data.

    Parameters:
        lat (float): latitude of the center point
        long (float): longitude of the center point

    Returns:
        gdf_list (list): list of GeoDataFrames containing the parking polygons
    """
    lat, long = coordinates[0], coordinates[1]
    point = Point(lat, long)
    point = gpd.GeoDataFrame(geometry=[point])

    # create a buffer around the center point to form a circle
    circle = point.buffer(config.NEIGHBORHOOD_DISTANCE)
    # create a GeoDataFrame from the circle
    circle_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(circle))
    bbox = circle_gdf.bounds  # calculate the bounding box from the circle

    # Extract the bounding box coordinates
    north, south, east, west = bbox["maxy"].values[0], bbox["miny"].values[0], \
    bbox["maxx"].values[0], \
        bbox["minx"].values[0]

    # Download the OSM data for surface parking lots
    tags = {'amenity': 'parking', 'parking:lane': 'surface'}
    parking_polygons_list = ox.geometries_from_bbox(north, south, east, west,
                                                    tags)

    # parking_polygons_list.plot()
    # plt.show()

    gdf_list = [gpd.GeoDataFrame(geometry=[polygon], crs='EPSG:4326') for
                index, polygon in
                parking_polygons_list['geometry'].items()]

    gdf_list[0].plot()
    plt.show()

    return gdf_list


def extract_OSM_street_data(polygon):
    """Extract OSM street data from the polygon.

    Parameters:
        polygon (Polygon): the polygon from which the OSM data has to be extracted

    Returns:
        street_graph (MultiDiGraph): the OSM street data
    """
    polygon_area = polygon.area  # calculate area of polygon in m2
    neighborhood_radius = math.sqrt(
        polygon_area / math.pi) + config.NEIGHBORHOOD_DISTANCE  # radius of OSM data
    polygon_centroid = polygon.centroid  # locate the center of the polygon
    circle = polygon_centroid.buffer(
        neighborhood_radius)  # create a buffer around the center point to form a circle
    circle_gdf = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries(circle))  # create a GeoDataFrame from the circle
    bbox = circle_gdf.bounds  # calculate the bounding box from the circle

    # Extract the bounding box coordinates
    north, south, east, west = bbox["maxy"].values[0], bbox["miny"].values[0], \
    bbox["maxx"].values[0], \
        bbox["minx"].values[0]

    street_graph = ox.graph_from_bbox(north, south, east, west,
                                      network_type='drive')  # save the OSM data

    return street_graph


def set_entrance_newest(polygon, graph, instance):
    """Set the entrance of the parking lot.

       Parameters:
           polygon (Polygon): The parking lot polygon
           graph (MultiDiGraph): The OSM street data
           instance (str): Instance name of the parking lot

       Returns:
           entry_edge (tuple): the edge of the graph that is the entrance of
           the parking lot
           nearest_street_point (Point): the point on the street that is the
           entrance of the parking lot
       """
    # Simplyfying the polygon
    polygon = polygon.simplify(tolerance=0.00001, preserve_topology=True)
    if isinstance(polygon, MultiPolygon):
        print("------------------------------------")
        polygon = max(polygon.geoms, key=lambda p: p.area)

    # Create the set of sides of the polygon
    polygon_corners = polygon.get_coordinates().values
    polygon_corners = polygon_corners[:-1]
    polygon_sides = []
    for i in range(len(polygon_corners)):
        start_point = polygon_corners[i]
        end_point = polygon_corners[(i + 1) % len(polygon_corners)]
        side = LineString([start_point, end_point])
        geod = Geod(ellps="WGS84")
        length = sum(geod.line_length([p[0] for p in segment.coords],
                                      [p[1] for p in segment.coords])
                     for segment in [side])
        if length >= 2:
            polygon_sides.append(side)

    # Create a set of streets as lines joining nodes
    street_segments = []

    for u, v, data in graph.edges(
            data=True):  # u and v are node IDs, data contains attributes
        if 'geometry' in data:
            line = data['geometry']  # Use existing geometry if available
        else:
            # Create a simple LineString from node coordinates if no geometry
            point_u = (graph.nodes[u]['x'], graph.nodes[u]['y'])
            point_v = (graph.nodes[v]['x'], graph.nodes[v]['y'])
            line = LineString([point_u, point_v])

        small_segments = split_line(line, segment_length=10)
        street_segments.extend(small_segments)

    min_distance = float(
        'inf')  # the minimum distance between street segments and polygon sides
    min_dist_edge_center = float(
        'inf')  # the minimum distance between the edge's center and polygon sides
    entry_edges = []  # the edge of the graph that is the entrance of the parking lot
    nearest_streets = []  # the street segment that is the entrance of the parking lot

    # Check for the shortest distance between street segments and polygon sides
    # and set it as the entrance
    for _ in range(1):
        entry_edges_temp = []
        for polygon_side in polygon_sides:
            if polygon_side in entry_edges:
                pass
            else:
                for street_segment in street_segments:
                    d = polygon_side.distance(street_segment)
                    angle = angle_between_lines(polygon_side, street_segment)

                    if -15 < angle < 15 or 165 < angle < 195:
                        if d < min_distance:
                            min_distance = d
                            entry_edges_temp.append(polygon_side)
                            nearest_streets.append(street_segment)
                            min_dist_edge_center = street_segment.distance(
                                polygon_side.centroid)
                        elif abs(d - min_distance) < config.EPSILON:
                            if street_segment.distance(
                                    polygon_side.centroid) < min_dist_edge_center:
                                min_distance = d
                                entry_edges_temp.append(polygon_side)
                                nearest_streets.append(street_segment)
                                min_dist_edge_center = street_segment.distance(
                                    polygon_side.centroid)
        entry_edges.append(entry_edges_temp[-1])

    for idx in range(len(entry_edges)):
        entry_edges[idx] = gpd.GeoDataFrame(geometry=[entry_edges[idx]],
                                            crs='EPSG:4326')
        nearest_streets[idx] = gpd.GeoDataFrame(geometry=[nearest_streets[idx]],
                                                crs='EPSG:4326')

    # Visualize the map on OSM
    fig, ax = ox.plot_graph(graph, bgcolor='#FFFFFF', node_color='#000000',
                            edge_color='#999999', show=False,
                            close=False, dpi=3000)

    polygon.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=1.75,
                 alpha=0.75)  # plot the polygon

    # # Plot the nearest point, entry edge and nearest street segment
    for entry_edge in entry_edges:
        entry_edge.plot(ax=ax, color='red')
    plt.savefig(f"./inputs/{instance}_OSM_map.png",
                bbox_inches='tight')  # save figure
    plt.close()

    return entry_edges, nearest_streets


def set_entrance_new(polygon, graph, instance):
    """Set the entrance of the parking lot.

    Parameters:
        polygon (Polygon): The parking lot polygon
        graph (MultiDiGraph): The OSM street data
        instance (str): Instance name of the parking lot

    Returns:
        entry_edge (tuple): the edge of the graph that is the entrance of
        the parking lot
        nearest_street_point (Point): the point on the street that is the
        entrance of the parking lot
    """
    # Create the set of sides of the polygon
    polygon_corners = polygon.get_coordinates().values
    polygon_corners = polygon_corners[:-1]
    polygon_sides = []
    for i in range(len(polygon_corners)):
        start_point = polygon_corners[i]
        end_point = polygon_corners[(i + 1) % len(polygon_corners)]
        side = LineString([start_point, end_point])
        polygon_sides.append(side)

    # Create a set of streets as lines joining nodes
    street_segments = []
    # Extract the coordinates of the edge's start and end nodes
    for edge in graph.edges(keys=False):
        start_point = (graph.nodes[edge[0]]['x'], graph.nodes[edge[0]]['y'])
        end_point = (graph.nodes[edge[1]]['x'], graph.nodes[edge[1]]['y'])
        segment = LineString([start_point, end_point])
        street_segments.append(segment)

    # The minimum distance between street segments and polygon sides
    min_distance = float('inf')
    # The minimum distance between the edge's center and polygon sides
    min_dist_edge_center = float('inf')
    # The edge of the graph that is the entrance of the parking lot
    entry_edges = []
    # The street segment that is the entrance of the parking lot
    nearest_streets = []

    # Check for the shortest distance between street segments and polygon sides
    # and set it as the entrance
    for _ in range(1):
        entry_edges_temp = []
        for polygon_side in polygon_sides:
            if polygon_side in entry_edges:
                pass
            else:
                for street_segment in street_segments:
                    d = polygon_side.distance(street_segment)
                    if d < min_distance:
                        min_distance = d
                        entry_edges_temp.append(polygon_side)
                        nearest_streets.append(street_segment)
                        min_dist_edge_center = street_segment.distance(
                            polygon_side.centroid)
                    elif abs(d - min_distance) < config.EPSILON:
                        if street_segment.distance(
                                polygon_side.centroid) < min_dist_edge_center:
                            min_distance = d
                            entry_edges_temp.append(polygon_side)
                            nearest_streets.append(street_segment)
                            min_dist_edge_center = street_segment.distance(
                                polygon_side.centroid)
        entry_edges.append(entry_edges_temp[-1])

    for idx in range(len(entry_edges)):
        entry_edges[idx] = gpd.GeoDataFrame(geometry=[entry_edges[idx]],
                                            crs='EPSG:4326')
        nearest_streets[idx] = gpd.GeoDataFrame(geometry=[nearest_streets[idx]],
                                                crs='EPSG:4326')

    # Visualize the map on OSM
    fig, ax = ox.plot_graph(graph, bgcolor='#FFFFFF', node_color='#000000',
                            edge_color='#999999', show=False,
                            close=False, dpi=3000)

    polygon.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=1.75,
                 alpha=0.75)  # plot the polygon

    # # Plot the nearest point, entry edge and nearest street segment
    for entry_edge in entry_edges:
        entry_edge.plot(ax=ax, color='red')
    plt.savefig(f"./inputs/{instance}_OSM_map.png",
                bbox_inches='tight')  # save figure
    plt.close()

    return entry_edges, nearest_streets


def angle_between_lines(polygon_edge, street_edge):
    x1, y1 = polygon_edge.coords[0]
    x2, y2 = polygon_edge.coords[1]
    x3, y3 = street_edge.coords[0]
    x4, y4 = street_edge.coords[1]

    # Convert to vectors
    v1 = numpy.array([x2 - x1, y2 - y1])
    v2 = numpy.array([x4 - x3, y4 - y3])

    # Compute dot product and magnitudes
    dot_product = numpy.dot(v1, v2)
    magnitude_v1 = numpy.linalg.norm(v1)
    magnitude_v2 = numpy.linalg.norm(v2)

    # Compute angle in radians
    angle_radians = numpy.arccos(dot_product / (magnitude_v1 * magnitude_v2))

    # Convert to degrees
    return numpy.degrees(angle_radians)


def split_line(line, segment_length=10):
    """Splits a LineString into segments of approximately `segment_length`
    meters."""
    gdf = gpd.GeoDataFrame(geometry=[line], crs="EPSG:4326")
    gdf = gdf.to_crs(
        "EPSG:3857")  # Convert to metric system for length calculation
    line_meters = gdf.geometry.iloc[0]

    if line_meters.length <= segment_length:
        return [line]  # If line is short, return as is

    num_segments = int(numpy.floor(
        line_meters.length / segment_length))  # ensure at least one segment
    segment_length = line.length / num_segments  # adjust segment length to
    # fit line evenly
    points = [line.interpolate(i * segment_length) for i in range(num_segments)]

    # Handle boundary points safely
    boundary_points = list(line.boundary.geoms) if hasattr(line.boundary,
                                                           "geoms") else [
        line.boundary]
    if len(boundary_points) == 2:
        last_point = boundary_points[1]
        if points[-1] != last_point:
            points.append(last_point)

    return [LineString([points[i], points[i + 1]]) for i in
            range(len(points) - 1)]


def set_entrance(polygon, graph, instance):
    """Set the entrance of the parking lot.

    Parameters:
        polygon (Polygon): The parking lot polygon
        graph (MultiDiGraph): The OSM street data
        instance (str): Instance name of the parking lot

    Returns:
        entry_edge (tuple): the edge of the graph that is the entrance
        of the parking lot
        nearest_street_point (Point): the point on the street that is the
        entrance of the parking lot
    """
    # Create the set of sides of the polygon
    polygon_corners = polygon.get_coordinates().values
    polygon_corners = polygon_corners[:-1]
    polygon_sides = []
    for i in range(len(polygon_corners)):
        start_point = polygon_corners[i]
        end_point = polygon_corners[(i + 1) % len(polygon_corners)]
        side = LineString([start_point, end_point])
        polygon_sides.append(side)

    # Create a set of streets as lines joining nodes
    street_segments = []
    # Extract the coordinates of the edge's start and end nodes
    for edge in graph.edges(keys=False):
        start_point = (graph.nodes[edge[0]]['x'], graph.nodes[edge[0]]['y'])
        end_point = (graph.nodes[edge[1]]['x'], graph.nodes[edge[1]]['y'])
        segment = LineString([start_point, end_point])
        street_segments.append(segment)

    entry_edges = []  # the edge of the graph that is the entrance
    nearest_streets = []  # the street segment that is the entrance
    min_distances = []

    for polygon_side in polygon_sides:
        entry_edges.append(polygon_side)
        min_distance = float('inf')
        street_segments_temp = []
        for street_segment in street_segments:
            d = polygon_side.distance(street_segment)
            if d < min_distance:
                min_distance = d
                street_segments_temp.append(street_segment)
        nearest_streets.append(street_segments_temp[-1])
        min_distances.append(min_distance)

    combined_edge_list = list(zip(entry_edges, min_distances))
    sorted_edge_list = sorted(combined_edge_list, key=lambda x: x[1])
    entry_edges = [item[0] for item in sorted_edge_list]

    combined_street_list = list(zip(nearest_streets, min_distances))
    sorted_street_list = sorted(combined_street_list, key=lambda x: x[1])
    nearest_streets = [item[0] for item in sorted_street_list]

    for idx in range(len(entry_edges)):
        entry_edges[idx] = gpd.GeoDataFrame(geometry=[entry_edges[idx]],
                                            crs='EPSG:4326')
        nearest_streets[idx] = gpd.GeoDataFrame(geometry=[nearest_streets[idx]],
                                                crs='EPSG:4326')

    # Visualize the map on OSM
    fig, ax = ox.plot_graph(graph, bgcolor='#FFFFFF', node_color='#000000',
                            edge_color='#999999', show=False,
                            close=False, dpi=3000)

    polygon.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=1.75,
                 alpha=0.75)  # plot the polygon

    # # Plot the nearest point, entry edge and nearest street segment
    for entry_edge in entry_edges:
        entry_edge.plot(ax=ax, color='red')
    for nearest_street in nearest_streets:
        nearest_street.plot(ax=ax,
                            color=[purple['r'], purple['g'], purple['b']],
                            linewidth=1.75)
    plt.savefig(f"./inputs/{instance}_OSM_map.png",
                bbox_inches='tight')  # save figure
    plt.close()

    return entry_edges, nearest_streets


def generate_grid_from_polygon(polygon, entry_edges, cell_size):
    """Generate the grid for the parking lot.

    Parameters:
        polygon (Polygon): the parking lot polygon
        entry_edges (tuple): the list of edges of the graph that form the entrance of the parking lot
        cell_size (float): the size of the grid cell

    Returns:
        num_rows (int): the number of rows in the grid
        num_cols (int): the number of columns in the grid
        entry_cells (tuple): the cell in the grid that is the entrance of the parking lot
        blocked_cells (list): the list of cells in the grid that are blocked
    """
    # Change the reference frame and define the target coordinate system
    target_crs = 'EPSG:26918'  # UTM Zone 18N (feet)
    # Project the polygon to the target coordinate system
    polygon = polygon.to_crs(target_crs)
    for idx in range(len(entry_edges)):
        entry_edges[idx] = entry_edges[idx].to_crs(target_crs)
    entry_edge_for_orientation = entry_edges[
        0]  # we orient the fishnet with respect to first entry edge

    # Compute the angle of rotation and get the coordinates of the end points
    end_point_data = entry_edge_for_orientation.get_coordinates().values
    x1 = end_point_data[0][0]
    x2 = end_point_data[1][0]
    y1 = end_point_data[0][1]
    y2 = end_point_data[1][1]

    # Calculate the angle between the line and the x-axis
    angle = math.degrees(numpy.arctan2((y1 - y2), (x2 - x1)))
    # print("rotation angle=", angle)

    # Rotate polygon
    polygon_centroid = polygon.geometry.centroid.iloc[0]
    polygon.geometry = polygon.geometry.apply(
        lambda x: rotate(x, angle, origin=polygon_centroid))
    entry_edge_for_orientation.geometry = entry_edge_for_orientation.geometry.apply(
        lambda x: rotate(x, angle, origin=polygon_centroid))

    # Set entry point to the center of the edge
    entry_points = []
    for idx in range(len(entry_edges)):
        entry_points.append(entry_edges[idx].geometry.centroid)

    # Create a fishnet over the polygon
    xmin, ymin, xmax, ymax = polygon.total_bounds  # define the bounding box for the fishnet
    num_rows = math.ceil((ymax - ymin) / cell_size)
    num_cols = math.ceil((xmax - xmin) / cell_size)
    fishnet_polygons = []
    blocked_cells = []
    entry_cells = []
    for i, j in itertools.product(range(num_cols), range(num_rows)):
        cell = Polygon([(xmin + i * cell_size, ymin + j * cell_size),
                        (xmin + (i + 1) * cell_size, ymin + j * cell_size),
                        (
                        xmin + (i + 1) * cell_size, ymin + (j + 1) * cell_size),
                        (xmin + i * cell_size, ymin + (j + 1) * cell_size)])
        fishnet_polygons.append(cell)
        overlap_ratio = cell.intersection(polygon).area.iloc[0] / cell.area
        if overlap_ratio <= config.CUTOFF_INTERSECTION_AREA:
            blocked_cells.append(((num_rows - 1) - j, i))
    fishnet = gpd.GeoDataFrame(geometry=gpd.GeoSeries(fishnet_polygons))
    for entry_point in entry_points:
        for i, j in itertools.product(range(num_cols), range(num_rows)):
            cell = Polygon([(xmin + i * cell_size, ymin + j * cell_size),
                            (xmin + (i + 1) * cell_size, ymin + j * cell_size),
                            (xmin + (i + 1) * cell_size,
                             ymin + (j + 1) * cell_size),
                            (xmin + i * cell_size, ymin + (j + 1) * cell_size)])
            if cell.contains(entry_point.iloc[0]) or cell.distance(
                    entry_point.iloc[0]) == 0:
                entry_cells.append(((num_rows - 1) - j, i))

    # Print the plot
    fig, ax = plt.subplots(figsize=(10, 10))
    fishnet.plot(ax=ax, edgecolor='gray', facecolor='none', alpha=0.5,
                 linewidth=0.5)
    polygon.plot(ax=ax, edgecolor='red', facecolor='none', alpha=0.75,
                 linewidth=4)
    entry_edge_for_orientation.plot(ax=ax, edgecolor=[purple['r'], purple['g'],
                                                      purple['b']],
                                    facecolor='none', alpha=1,
                                    linewidth=3)
    entry_edge_for_orientation.geometry.centroid.plot(ax=ax, color=[purple['r'],
                                                                    purple['g'],
                                                                    purple[
                                                                        'b']],
                                                      markersize=60)
    plt.savefig(f"./inputs/{config.instance}_initial_layout.png",
                bbox_inches='tight')
    plt.close()
    return num_rows, num_cols, entry_cells, blocked_cells


def adjust_entrance(num_rows, num_cols, drive_field_width, entry_cells,
                    blocked_cells):
    """Make adjustments to the entry cell and blocked cells to ensure that the driveway falls within the grid

    Parameters:
        num_rows (int): the number of rows in the grid
        num_cols (int): the number of columns in the grid
        drive_field_width (int): the width of the driveway
        entry_cell (tuple): the entry cell
        blocked_cells (list): the list of blocked cells

    Returns:
        entry_cells (tuple): the entry cell
        blocked_cells (list): the list of blocked cells
    """

    entry_cell = entry_cells[0]
    if config.ARE_DRIVE_LANES_ONEWAY:
        d = drive_field_width * 2
    else:
        d = drive_field_width
        # Adjustments to make sure entry driveway falls within the grid
    i = entry_cell[0]  # row number of entry cell
    j = entry_cell[1]  # column number of entry cell
    if i + (d) > num_rows:
        i = num_rows - d
    if j + d > num_cols:
        j = num_cols - d
    entry_cell = (i, j)

    # Iterate through driveway cells anchored at entry_cells_selected
    for i, j in itertools.product(range(entry_cell[0], entry_cell[0] + d),
                                  range(entry_cell[1], entry_cell[1] + d)):
        # check if any of these driveway cells are blocked
        if (i, j) in blocked_cells:
            # If blocked, then revert them back to being a normal cell
            blocked_cells = [item for item in blocked_cells if
                             item != (i,
                                      j)]  # If blocked, then revert them

    # clearing up way above the entrance for vehicle to enter
    for i, j in itertools.product(
            range(max(0, entry_cell[0] - d), entry_cell[0]),
            range(entry_cell[1], entry_cell[1] + d)):
        # check if any of these driveway cells are blocked
        if (i, j) not in blocked_cells:
            # If blocked, then revert them back to being a normal cell
            blocked_cells += [(i, j)]  # Add to blocked field

    return entry_cell, blocked_cells
