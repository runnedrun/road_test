$(function(){
	var map = $("#map")[0];		
	var actualLocations = new Container();
	var perceivedLocations = new Container();
	var destinations = new Container();
	var turns = new Container();
	var updater = LocationUpdater(1000, actualLocations, perceivedLocations, destinations, turns) 	

	Api.gridData().then(function(resp){		
		var actualRenderer = new Renderer(map, 500, 1000, resp.intersections, actualLocations, destinations, turns);	
	})	
})

Renderer = function(mapCanvas, gridSize, renderFrequency, intersections, carLocations, destinations, turns) {		
	// destinations and  turns are optional
	destinations = destinations || new Container()	
	turns = turns || new Container()

	var spriteHeight = 20
	var spriteWidth = 30
	context = mapCanvas.getContext("2d");
	var $carImage = $("#car-template");	
	var carImage = $carImage[0]
	mapCanvas.width = gridSize;
	mapCanvas.height = gridSize;

	function renderGrid() {			
		// if we get the unique of all the x and y coords of each intersection, then we'll have the starting
		// x and y for each grid line.
		var verticalGridLinesX = new Set();
		var horizontalGridLinesY = new Set();
		
		intersections.forEach(function(intersection) {			
			x = Number(intersection[0])
			y = Number(intersection[1])

			// first draw the intersection, then get the x and y coords for drawing grid lines			
			
			context.beginPath();
			context.arc(x, y, 5, 0, 2*Math.PI);
			context.closePath();
			context.stroke();						

			// we dont want to add grid lines for the intersections which are at the border
			x > 0 && x < gridSize && verticalGridLinesX.add(intersection[0]);
			y > 0 && y < gridSize && horizontalGridLinesY.add(intersection[1]);			
		})

		verticalGridLinesX.forEach(function(x) {			
			context.moveTo(x, 0);
			context.lineTo(x, gridSize);
		})

		horizontalGridLinesY.forEach(function(y) {			
			context.moveTo(0, y);
			context.lineTo(gridSize, y);
		})
		
		context.strokeStyle = "black";
		context.stroke();
	}

	function render() {		
		context.clearRect(0, 0, gridSize, gridSize)
		
		renderGrid()

		carLocations.get().forEach(function(location) {
			carId = location[0]
			coords = location[1] 
			x = coords[0]
			y = coords[1]			
			context.drawImage(carImage, x - spriteWidth / 2, y - spriteHeight / 2, spriteWidth, spriteHeight)
		});

		destinations.get().forEach(function(dest){
			carId = dest[0]
			coords = dest[1] 
			x = coords[0]
			y = coords[1]
			context.font = "20px Arial"
			context.fillStyle = "green";
			context.textAlign = "center";
			console.log("rendering destination for " + carId + ": ", x, y)
			context.fillText(carId, x, y + 10);			
		})
		
		turns.get().forEach(function(turnList){
			carId = turnList[0]
			turnsForCar = turnList[1] 			
			turnsForCar.forEach(function(turn){				
				turnStart = turn[0];
				turnEnd = turn[1];

				startX = turnStart[0];
				startY = turnStart[1];

				endX = turnEnd[0];
				endY = turnEnd[1];

				context.font = "20px Arial"
				context.fillStyle = "blue";
				context.textAlign = "center";
				console.log("rendering turn for " + carId + ": ", turnStart, turnEnd);
				context.fillText(carId, startX, startY + 10);				
			})			
		})

		requestAnimationFrame(render);
	}	

	requestAnimationFrame(render);
}

Container = function() {
	var locations = []	
	var self = this;

	self.update = function(newLocations) {
		// format of the location response is { carID: [car x, car y] }
		locations.splice(0, locations.length);
		$.each(newLocations, function(i, location) {
			locations.push(location)
		})		
	}

	self.get = function() { return locations }	
}

LocationUpdater = function(updateFrequency, actualLocations, perceivedLocations, destinations, turns) {	
	function updateLocations(resp) { 
		console.log("updating");
		actualLocationsList = []
		carDestinationsList = []
		turnList = []
		Object.keys(resp.actual).forEach(function(k){
			actualLocationsList.push([k, resp.actual[k].pos]);
			carDestinationsList.push([k, resp.actual[k].dest]);			
			turnList.push([k, resp.actual[k].turns]);
		})
		actualLocations.update(actualLocationsList);		
		destinations.update(carDestinationsList);
		turns.update(turnList);
	}

	function requestUpdate() {
		Api.carLocations().then(updateLocations);
	}

	setInterval(requestUpdate, updateFrequency);	
}

Api = new (function() {
	var self = this;

	function onError(resp) {
		console.log("failed to get car locations: " + resp)
	}

	self.carLocations = function() {
		return $.ajax({
			url: "http://localhost:8000/car_locations",
			dataType: "json",			
			error: onError
		})	
	}

	self.gridData = function() {
		return $.ajax({
			url: "http://localhost:8000/grid_data",
			dataType: "json",			
			error: onError
		})	
	}
})()
