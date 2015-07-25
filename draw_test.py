import multiprocessing as mp
import random
import networkx as nx
import time
from navigation_server import *

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

class Roadmap: 
	def __init__(self, horizontal_roads, vertical_roads, road_graph): 
		self.graph = road_graph
		self.horiz_roads = horizontal_roads
		self.vert_roads = vertical_roads

	def get_possible_next_locations(self, pos):
		x = pos[0]
		y = pos[1]

		on_vertical_road = False
		on_horizontal_road = False

		for road in self.vert_roads:
			on_vertical_road = x == road 

		for road in self.horiz_roads:
			on_horizontal_road = y == road


		posssible_locations = []

		if on_vertical_road and on_horizontal_road:
			# we are at an intersection			
			posssible_locations = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
		elif on_vertical_road:					
			posssible_locations = [(x, y - 1), (x, y + 1)]
		else:						
			posssible_locations = [(x - 1, y), (x + 1, y)]

		# don't return a next location that is off the map
		return [loc for loc in posssible_locations if loc[0] >= 0 and loc[1] >= 0] 

class Car():
	def __init__(self, car_id, roadmap, actual_car_locations, starting_pos, starting_velocity): 
		self.navigation_client = NavigationClient(1060)
		self.pos = starting_pos
		self.velocity = starting_velocity
		self.roadmap = roadmap
		self.id = car_id
		self.actual_car_locations = actual_car_locations

	def drive(self):
		possible_next_positions = self.roadmap.get_possible_next_locations(self.pos)

		# calcuate the next valid position for the car to go
		next_position = False
		for move in possible_next_positions:
			x_move = move[0] - self.pos[0] 
			y_move = move[1] - self.pos[1]

			# if the next position is in the direction the car is going, move there
			if self.velocity[0] and x_move / self.velocity[0] >= 0:
				next_position = move
			elif self.velocity[1] and  y_move / self.velocity[1] >= 0:
				next_position = move

		# if there are no possible positions given the current velocity choose a random 
		# next position from the possible positions. (make a turn)
		if not next_position and possible_next_positions:
			next_position = random.choice(possible_next_positions)

		# if there are no possible positions at all, I guess we're off road, do nothing.
		if not possible_next_positions:
			print("no locations to move to!")
			return

		# TODO: move based on velocity magnitude

		x_diff = next_position[0] - self.pos[0]
		y_diff = next_position[1] - self.pos[1]

		# the new velocity for either direction is either 0, or the curent velocity, but going in the direction
		# which the car has turned.
		new_vx = x_diff and self.velocity[0] * x_diff / abs(x_diff)
		new_vy = y_diff and self.velocity[1] * y_diff / abs(y_diff)

		print("next valid pos is: " + str(next_position))
		print("current is: " + str(self.pos))

		self.pos = next_position
		self.actual_car_locations[self.id] = self.pos

road_map = Roadmap(road_graph, horiz_roads, vert_roads)

start = random.choice(road_graph.nodes())

actual_car_locations = {}

car = Car(1, road_map, actual_car_locations, start, (1,0))

cars = [car]

server = NavigationServer(actual_car_locations, 8000).start()

while True:
	time.sleep(.5)
	for car in cars:
		print("dirving cars")
		car.drive()