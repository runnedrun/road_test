import threading
import urllib.request, urllib.parse, urllib.error 
import sys
import json
import http.server

class NavigationServer():
	# car locations is a map from car id to lat lon coordinates.
	def __init__(self, cars, road_map, port = 1060):
		# The navigation handler is defined within this init so that it has access to the map of actual car locations

		# We also need a map of perceived car locations which can be updated on posts, and returned on gets.
		perceived_car_locations = {}

		class NavigationRequestHandler(http.server.SimpleHTTPRequestHandler):
			def do_POST(self):
				if (self.path == "/navigate"):
					print("navigating")

					content_len = int(self.headers.get("content-length", 0))
					body = json.loads(self.rfile.read(content_len).decode("UTF-8"))
					car_id = body["id"]
					position = tuple(body["position"])
					dest = tuple(body["dest"])
					vel = tuple(body["velocity"])
					turns = road_map.navigate(position, vel, dest)

					perceived_car_locations[car_id] = position

					print("id " + str(car_id))
					print("position " + str(position))
					print("dest " + str(dest))
					print("vel " + str(vel))
					print("sending back turns" + str(turns))

					body = {"turns": turns}
					self.render_response(body)

				else:
					self.send_response(404)

			def do_GET(self):
				if (self.path == "/car_locations"):
					perceived = [(id, location) for id, location in perceived_car_locations.items()]
					# actual = [(id, location) for id, location in actual_car_locations.items()]					
					actual = {}
					for car in cars:
						actual[car.id] = {"dest": car.dest, "pos": car.pos}

					body = {"actual": actual, "perceived": perceived}
					self.render_response(body)					
					return

				elif (self.path == "/grid_data"):
					intersections = road_graph.nodes()					
					body = {"intersections": intersections}
					self.render_response(body)
					return
				else:
					super().do_GET()

			def render_response(self, resp_obj):
				body_str = json.dumps(resp_obj)					
				self.send_response(200)	
				self.wfile.write(bytes(body_str, "UTF-8"))
			

		self.server = http.server.HTTPServer(("localhost", port), NavigationRequestHandler)
		self.cars = cars
		self.perceived_car_locations = perceived_car_locations


	def start(self):
		print("STARING")
		threading.Thread(target = self.server.serve_forever).start()		


class NavigationClient():
	def __init__(self, port):
		self.port = port

	def navigate(self, id, position, vel, dest):
		body = {"id": id, "position": position, "dest": dest, "velocity": vel}
		body_str = json.dumps(body)
		# try: 
		resp = urllib.request.urlopen("http://localhost:" + str(self.port) + " /navigate", data = bytes(body_str,"UTF-8"))
		print("got resp" + str(resp))			
		resp_dict = json.loads(resp)
		return resp_dict["turns"]

		# except:
		# 	e = sys.exc_info()[0]
		# 	print(e)			
	
# server = NavigationServer({}, 1060)
# client = NavigationClient(1060)