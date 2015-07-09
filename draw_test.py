import pyglet
import multiprocessing as mp
import random
import networkx as nx

grid_size = 500
number_of_streets = 10 

# grid is made up of 2 sets, one for x location for vertical roads, and one for y location for horizontal roads
vert_roads = set()
horiz_roads = set()
road_graph = nx.Graph()

for i in range(0, number_of_streets):
	if (i % 2 == 0):
		vert_roads.add(random.randrange(grid_size))
	else:
		horiz_roads.add(random.randrange(grid_size))

for start_x in vert_roads:
	for start_y in horiz_roads:
		road_graph.add_node((start_x, start_y))

vert_list = list(vert_roads)
horiz_list = list(horiz_roads)

vert_list.sort()
horiz_list.sort()


# add vertical edges
for x in vert_list:
		# add the first edge which starts from the boundary of the grid
		distance = horiz_list[0]
		edge_intersection = (x, 0)
		road_graph.add_node(edge_intersection)
		road_graph.add_edge((x, distance), edge_intersection, weight = distance, distance = distance)

		for i, y in enumerate(horiz_list):		
			# if there are no more intersections then make an intersection at the edge of the grid
			next_index = i + 1
			prev_index = i - 1
			if (next_index) >= len(horiz_list):
				distance = grid_size - y
				edge_intersection = (x, grid_size)
				road_graph.add_node(edge_intersection)
				road_graph.add_edge((x, y), edge_intersection, weight = distance, distance = distance)
			else:
				next_y = horiz_list[next_index]
				distance = next_y - y
				road_graph.add_edge((x, y), (x, horiz_list[i + 1]), weight = distance, distance = distance)		

# add horizontal edges
for y in horiz_list:
		# add the first edge which starts from the boundary of the grid
		distance = vert_list[0]
		edge_intersection = (0, y)
		road_graph.add_node(edge_intersection)
		road_graph.add_edge((distance, y), edge_intersection, weight = distance, distance = distance)

		for i, x in enumerate(vert_list):		
			# if there are no more intersections then make an intersection at the edge of the grid
			if (i + 1) >= len(vert_list):
				distance = grid_size - x
				edge_intersection = (grid_size, y)
				road_graph.add_node(edge_intersection)
				road_graph.add_edge((x, y), edge_intersection, weight = distance, distance = distance)
			else:
				next_x = vert_list[i + 1]
				distance = next_x - x
				road_graph.add_edge((x, y), (vert_list[i + 1], y), weight = distance, distance = distance)

class Car():
	def __init__(self, name, starting_pos): 
		self.name = name
		self.pos = starting_pos

	def draw(self):
		pyglet.graphics.draw(1, pyglet.gl.GL_POINTS, ('v2i', self.pos))

window = pyglet.window.Window(width = grid_size, height = grid_size)
window.clear()

def draw_streets(dt):	
	for start in horiz_roads:
		pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2i', (0, start, grid_size, start)))
		
	for start in vert_roads:
		pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2i', (start, 0, start, grid_size)))

	for intersection in road_graph.nodes():
		pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2i', (
			intersection[0] + 4, intersection[1] + 4,
			intersection[0] + 4, intersection[1] - 4,
			intersection[0] - 4, intersection[1] + 4,
			intersection[0] - 4, intersection[1] - 4,
			)),('c3B', (255, 0, 0, 255, 0, 0, 255, 0, 0, 255, 0, 0)))


# mp.set_start_method('fork')
# mp.Queue() # presumably a thread safe queue
# mp.Process(target = pyglet.app.run)

# pyglet.clock.schedule_interval(draw_streets, .1)

pyglet.clock.schedule_once(draw_streets, .1)

pyglet.app.run()