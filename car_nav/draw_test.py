import multiprocessing as mp
import random
import networkx as nx
import time
import pdb
from navigation_server import *
from enum import Enum

#### This implementation assumes that all roads are either vertical or horizontal. 
#### If this changes, then the code will have to change too.

grid_size = 500
number_of_streets = 10 

# grid is made up of 2 sets, one for x location for vertical roads, and one for y location for horizontal roads
vert_roads = set()
horiz_roads = set()
road_graph = nx.Graph()

# generate a bunch of roads, but not on the boundary of the map
for i in range(0, number_of_streets):
	if (i % 2 == 0):
		vert_roads.add(random.randrange(1, grid_size - 1))
	else:
		horiz_roads.add(random.randrange(1, grid_size - 1))

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
	def __init__(self, road_graph): 
		self.graph = road_graph		
		self.horiz_roads = set()
		self.vert_roads = set()
		for node in self.graph.nodes():
			self.vert_roads.add(node[0])
			self.horiz_roads.add(node[1])

	def __get_edge_coords(self, edge):
		x1 = edge[0][0]
		x2 = edge[1][0]
		y1 = edge[0][1]
		y2 = edge[1][1]					

		xs = [x1, x2]
		xs.sort()

		ys = [y1, y2]
		ys.sort()

		return xs, ys

	def __get_edges_pos_is_on(self, pos):
		cur_x = pos[0]
		cur_y = pos[1]	

		edges = []		
		for edge in road_graph.edges():
			xs, ys = self.__get_edge_coords(edge)	
			cur_x_on_edge = xs[0] <= cur_x <= xs[1] 			
			cur_y_on_edge = ys[0] <= cur_y <= ys[1] 

			if  cur_x_on_edge and cur_y_on_edge:
				edges.append(edge)

		return edges

	def __get_next_intersection(self, pos, vel):		
		vx = vel[0]
		vy = vel[1]			

		possible_edges = self.__get_edges_pos_is_on(pos)

		print("pssibles for " + str(pos) + ": " + str(possible_edges))

		for edge in possible_edges:
			xs, ys = self.__get_edge_coords(edge)
			vertical_edge = xs[0] == xs[1]
			horizontal_edge = ys[0] == ys[1]			

			# with this logic its possible that a car can be on multiple edges,
			# if it is currently on a intersections. If this is the case we'll just treat it
			# as on the first edge we find, and things should work out because the car
			# will eventually get to the node we return.			

			if horizontal_edge and vx:												
				if vx >= 0:
					return (xs[1], ys[0])
				else:
					return (xs[0], ys[0])

			elif vertical_edge and vy:								
				if vy >= 0:
					return (xs[0], ys[1])
				else:
					return (xs[0], ys[0])

		print("failed to find the next intersection for some reason")


	def navigate(self, cur_pos, cur_vel, dest_pos):
		if (not road_graph.has_node(dest_pos)):
			print("DESTINATION NOT ON MAP: " + str(road_graph.nodes()))
			return []
		
		cur_x = cur_pos[0]
		cur_y = cur_pos[1]
		vx = cur_vel[0]
		vy = cur_vel[1]
				
		next_node = self.__get_next_intersection(cur_pos, cur_vel)

		print("next: " + str(next_node) + " and current: " + str(cur_pos))

		if next_node == dest_pos:
			print("no navigation instructions, becauase we are on track to arrive without further turns")
			return []

		if not next_node:
			print("we can't navigate for some reason!")
			return []
			# raise ValueError("Navigation failed.")

		path = nx.shortest_path(road_graph, next_node, dest_pos)

		# now build a list of turns. Each turn is represented as a pair: (intersection, next point to move to).
		# example: ((10,20), (10, 21)) indicates that when the car reachs the intersection at 10, 20 it should move 
		# in the direction of 10,21.
		turns = []
		for i, node in enumerate(path):			
			on_last_node = i + 1 >= len(path)
			if not on_last_node:
				next_node = path[i+1]

				x1 = node[0]
				x2 = next_node[0]

				y1 = node[1]
				y2 = next_node[1]

				vertical_edge = x1 == x2
				horizontal_edge = y1 == y2
				
				if horizontal_edge:
					direction = (x1 - x2) / abs(x1 - x2)
					turns.append((node, (x1 + direction, y1)))
				else:
					direction = (y1 - y2) / abs(y1 - y2)
					turns.append((node,(x1, y1 + direction)))
		print("returning turns: " + str(turns))
		return turns				



	def get_possible_next_locations(self, pos):	
		x = pos[0]
		y = pos[1]

		edges = self.__get_edges_pos_is_on(pos)

		posssible_locations = []
		for edge in edges:
			xs, ys = self.__get_edge_coords(edge)
			horizontal = ys[0] == ys[1]
			vertical = xs[0] == xs[1]

			# we should not add possible possitions which aren't actually on the edge.
			# This can occur if we are on a node. We will filter out Falses later on.			
			if horizontal:								
				posssible_locations.extend([x + 1 <= xs[1] and (x + 1, y), x - 1 >= xs[0] and (x - 1, y)])
			else:
				posssible_locations.extend([y + 1 <= ys[1] and (x, y + 1), y - 1 <= ys[0] and (x, y - 1)])

		# filter out positiosn which aren't on an edge		
		print("returning these possible locations: " + str(posssible_locations))
		return [loc for loc in posssible_locations if loc] 

class Direction(Enum):
	horizontal = 0
	vertical = 1

class NodeData():
	def __init__(self, coords):
		self.x = coords[0]
		self.y = coords[1]

class EdgeData():
	def __init__(self, node1, node2):		
		xs = [node1.x, node2.x]
		xs.sort()

		ys = [node1.y, node2.y]
		ys.sort()		

		# start is the lowest node (x or y closest to 0, depending on direction)		
		if (xs[0] == xs[1]):
			self.direction = Direction.vertical

			if (node1.y == ys[0]):
				self.start = node1
				self.end = node2
			else:
				self.start = node2
				self.end = node1
		else:
			self.direction = Direction.horizontal

			if (node1.x == xs[0]):
				self.start = node1
				self.end = node2
			else:
				self.start = node2
				self.end = node1
		

		

class Car():
	def __init__(self, car_id, roadmap, dest, starting_pos, starting_velocity): 
		self.navigation_client = NavigationClient(8000)
		self.pos = starting_pos
		self.velocity = starting_velocity
		self.roadmap = roadmap
		self.id = car_id
		self.actual_car_locations = actual_car_locations
		self.dest = dest

		# this will be populated by the __get_navigation method when it is called
		self.turns = []
		self.turns_hash = {}

	# make a request to the navigation server to get a list of directions
	def __update_navigation(self):		
		self.turns = self.navigation_client.navigate(self.id, self.pos, self.velocity, self.dest)		
		for turn_start, turn_end in self.turns:			
			self.turns_hash[tuple([int(x), int(y) for x, y in turn_start)] = tuple(turn_end)

	def drive(self):
		self.__update_navigation()

		if self.pos == dest:
			print("ARRIVED AT DESTINATION!")
			return 

		possible_next_positions = self.roadmap.get_possible_next_locations(self.pos)		

		# calcuate the next valid position for the car to go
		next_position = False
		for move in possible_next_positions:
			x_move = move[0] - self.pos[0] 
			y_move = move[1] - self.pos[1]

			# if we are at a turn start, and one of the next positions is a turn end, go there
			turn_end = self.turns_hash.get(self.pos, False)
			if turn_end:				
				next_position = turn_end
				break

			# if the next position is in the direction the car is going, move there
			if self.velocity[0] and x_move / self.velocity[0] >= 0:
				next_position = move
				break
			elif self.velocity[1] and  y_move / self.velocity[1] >= 0:
				next_position = move
				break

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

		# if no turn has been made, then maintain the current velocity, otherwise the velocity for the direction
		# of the turn becomes +-1
		vx = self.velocity[0]
		vy = self.velocity[1]

		new_vx = (not x_diff and vx) or (x_diff and x_diff / abs(x_diff))
		new_vy = (not y_diff and vy) or (y_diff and y_diff / abs(y_diff))

		# print("next valid pos is: " + str(next_position))
		# print("current is: " + str(self.pos))

		self.pos = tuple(next_position)
		self.velocity = (new_vx, new_vy)
		# print("velocity is now: " + str(self.velocity))

road_map = Roadmap(road_graph)

nodes = road_graph.nodes()
start = random.choice(nodes)
nodes.remove(start)
start = (start[0], 0)
dest = random.choice(nodes)

actual_car_locations = {}

car = Car(1, road_map, dest, start, (1,0))

cars = [car]

server = NavigationServer(cars, road_map, 8000).start()

while True:
	time.sleep(.1)
	for car in cars:
		car.drive()