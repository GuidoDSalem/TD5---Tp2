import json
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random

def generate_random_json(
        num_services=8, 
        num_stations=2, 
        max_time=1440, # 1440 minutos === 60*24 minutos === 1 dia
        demand_value=500, 
        capacity=100, 
        max_rs=25,
        seed = 40,
        time_beetween_services = 58,
        cost_per_unit = 1.0
        ):
    
    random.seed(seed)
    stations = [f"{i}Station" for i in range(num_stations)]
    services = {}
    
    for service_id in range(1, num_services + 1):
        stops = []
        time = random.randint(0, max_time - time_beetween_services)
        stationD = random.choice(stations)
        stationA = random.choice(stations)
        while stationD == stationA:
            stationA = random.choice(stations)
        stop = {
            "time": time,
            "station": stationD,
            "type": "D"
        }
        stops.append(stop)
        stop = {
            "time": time + time_beetween_services,
            "station": stationA,
            "type": "A"
        }
        stops.append(stop)
        services[str(service_id)] = {
            "stops": stops,
            "demand": [demand_value]
        }
    
    cost_per_unit = {station: cost_per_unit for station in stations}

    data = {
        "services": services,
        "stations": stations,
        "cost_per_unit": cost_per_unit,
        "rs_info": {
            "capacity": capacity,
            "max_rs": max_rs
        }
    }
    
    return data

def getDatafromPath(path):
    with open(path) as json_file:
        data = json.load(json_file)
        json_file.close()
    return data

def get_node_name(time:int,station:str):
    name = str(time)
    while len(name) < 4:
        name = '0' + name
    return name +"_" +station[:2]

def sort_nodes(nodes:list):
    sorted_nodes = []
    for i in range(len(nodes)):
        value = int(nodes[i][:4])
        sorted_nodes.append(value)
    sorted_nodes.sort()
    for i in range(len(sorted_nodes)):
        sorted_nodes[i] = get_node_name(sorted_nodes[i],nodes[i][5:])
    return sorted_nodes

def getPos(data):
	
	servicios:dict = data["services"]
	pos = {}
	for i, estacion in enumerate(data["stations"]):
		columna = []
		for key, value in servicios.items():
			
			if value["stops"][0]["station"] == estacion:
					name_value = get_node_name(value["stops"][0]["time"],value["stops"][0]["station"])
					columna.append(name_value)
			if value["stops"][1]["station"] == estacion:
					name_value = get_node_name(value["stops"][1]["time"],value["stops"][1]["station"])
					columna.append(name_value)

		columna = sort_nodes(columna)
		columna.reverse()
		for j, value in enumerate(columna):
			pos[value] = (i,j)

	return pos

def get_curved_edges(G):
	edges = []
	for u,v in G.edges():
		if u[:4] > v[:4]:
			edges.append((u,v))
	return edges

def printGraph(G,data,flow_dict):
	
    # Crear etiquetas para los bordes que muestren peso, capacidad y flujo
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        if u in flow_dict and v in flow_dict[u]:
	    # f"w={d['weight']}, c={d['capacity']}, f={flow_dict[u][v]}" POR LAS DUDAS
            edge_labels[(u, v)] = f"w={d['weight']},f={flow_dict[u][v]}"
        else:
            print(f"Missing flow for edge ({u}, {v})")
    
    # Asignar colores a los nodos y bordes
    node_colors = [G.nodes[node]['color'] for node in G.nodes()]
    edge_colors = [G[u][v]['color'] for u, v in G.edges()]
    edges_curves = [G.edges()]
    
    edges_with_curves = get_curved_edges(G)  
    
    edge_styles = ['arc3, rad=0.45' if (u, v) in edges_with_curves else 'arc3, rad=0' for u, v in G.edges()]

    pos = getPos(data)


    plt.figure(figsize=(8, 8))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors)
    nx.draw_networkx_labels(G, pos, font_weight='bold')

    for (u, v), style in zip(G.edges(), edge_styles):
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color=[G[u][v]['color']], connectionstyle=style)
    
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
	# Ajustar la posición de las etiquetas de los bordes curvados
    label_pos_adjust = {}
    for (u, v) in edges_with_curves:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        label_pos_adjust[(u, v)] = ((x1 + x2) / 2  , (y1 + y2) / 2 + 0.1)

    # Dibujar etiquetas manualmente para bordes con curvas
    for (u, v), (x, y) in label_pos_adjust.items():
        plt.text(x+0.1, y, edge_labels[(u, v)], fontsize= 12, ha='left')
    
    plt.show()



def addService(service, G):
    ## haces los nodos
	id, data = service
	from_station = data["stops"][0]["station"]
	to_station = data["stops"][1]["station"]
	from_time = data["stops"][0]["time"]
	to_time = data["stops"][1]["time"]
	demand = data["demand"]



def addNodesAndTrainEdges(data, G): 
    ## agrega los trenes de viaje 
	services = data["services"]
	estacion = None
	for service in services.items():
		id , data_ = service
		from_station = data_["stops"][0]["station"]
		to_station = data_["stops"][1]["station"]
		from_time = data_["stops"][0]["time"]
		to_time = data_["stops"][1]["time"]
		capacidad = data["rs_info"]["capacity"]
		demand = data_["demand"][0]
		flow = int(np.ceil(demand/capacidad))

		from_ = get_node_name(from_time,from_station)
		to_ = get_node_name(to_time,to_station)
		G.add_node(from_,demand = flow, color='blue')
		G.add_node(to_, demand= -flow, color='red')
		G.add_edge(from_, to_, weight= 0,capacity = data["rs_info"]["max_rs"] - flow, color='green' )
		

def addTraspasoEdges(data, G):
	## conecta dos eventos consecutivos 
	for station in data["stations"]:
		station_nodes = []

		for key, value in data["services"].items():
			stops = value["stops"]
			for stop in stops:
				if stop["station"] == station:
					station_nodes.append(stop["time"])
		#station_nodes = station_nodes.sort() # TAL VEZ HAYA QUE ORDENAR ESTA LISTA
		station_nodes.sort()
		
		station_nodes = [get_node_name(station_nodes[i],station) for i in range(len(station_nodes))]
		for i in range(len(station_nodes)-1):
			G.add_edge(station_nodes[i], station_nodes[i+1], weight=0, capacity=data["rs_info"]["max_rs"] ,color='blue')
            

def getFirstDeparture(estacion, data, G): 
    ## primer servicio del diaa
	res = 10000000000000
	for key, value in data["services"].items():  
		stops = value["stops"]
		for stop in stops:
			if stop["time"] < res and stop["station"] == estacion: # Quiero encontrar el horario de la 1ra departure de la estación
				res = stop["time"]
	return get_node_name(res, estacion)

def getLastArrival(estacion, data, G):
    ## ultimo servico del dia
    res = -1
    for key, value in data["services"].items(): 
        stops = value["stops"]
        for stop in stops:
            if stop["station"] == estacion and stop["time"] > res: # Quiero encontrar el horario del último arrival a la estación
                res = stop["time"]
    return get_node_name(res, estacion)

def addTrasNocheEdges(data, G, modificacion_trasnoche): 
	## agregas las aristas de trasnoche 
	for estacion in data["stations"]:
		inicio = getFirstDeparture(estacion, data, G)
		final = getLastArrival(estacion, data, G)
		if(modificacion_trasnoche[1] == estacion):
			G.add_edge(final, inicio, weight=1,capacity = data["rs_info"]["max_rs"] - modificacion_trasnoche[0],color='red')
		else:
			G.add_edge(final, inicio, weight=1,capacity = data["rs_info"]["max_rs"],color='red')
	pass

def generateGraph(data,modificaciones_trasnoche):

	G = nx.DiGraph()

	addNodesAndTrainEdges(data, G)
	addTraspasoEdges(data, G)
	addTrasNocheEdges(data, G,modificaciones_trasnoche)

	return G
	
def costo_minimo(flowDict,G):

    for u, v  in G.edges:
        if G.edges[u,v]['color'] == 'green':
            flowDict[u][v] += G.nodes[u]["demand"] 
            

    
def vagones_totales(flowDict,data, G):
	flujo_estacion = 0

	for estacion in data["stations"]:
		inicio = getFirstDeparture(estacion, data, G)
		final = getLastArrival(estacion, data, G)
		flujo_estacion = flowDict[final][inicio]
  
		print(F"{estacion}: {flujo_estacion} vagones")
	

				
					
def getFlowCost(flowDict, G):
	cost = 0
	for u,v in G.edges:
		cost += flowDict[u][v] * G.edges[u,v]['weight']
	return cost     
	
def main():
	print("Elegi una instancia:")
	instance = int(input("Instancia 1: Toy instance \nInstancia 2: Cronograma real \nInstancia 3: Random Generated Instance\n"))

	if(instance <= 2):
		#ejercicio: algoritmo e implementacion
		if(instance == 1):
			filename = "instances/toy_instance.json"

		#ejercicio: datos parte real
		else:
			filename = "instances/retiro-tigre-semana.json"
   
		data = getDatafromPath(filename)
	#ejercicio: datos parte de generar cronogramas
	else:
		numero_servicios = int(input("Elegi una cantidad de servicios: "))
		numero_estaciones = int(input("Elegi cantidad de estaciones: "))
		data = generate_random_json(num_services=numero_servicios, num_stations=numero_estaciones,seed=42)
	
	reduccion = int(input("Hay problemas de mantenimiento? \nSi = 1 \nNo = 2\n"))
	
 	#ejercicio: escenario adicional
	if(reduccion == 1):
		services = data["services"]
		estaciones = []
		for service in services.items():
			if data["stops"][0]["station"] not in estaciones:
				estaciones.append(data["stops"][0]["station"])
		print(estaciones)
  
		nombre_estacion = input("Escriba el nombre de la estacion que tendra una reduccion: ")
		num_reduccion = input("Indique la reduccion de la cantidad de unidades en la cabecera: ")
		REDUCCION_CAPACIDAD_TRASNOCHE = (num_reduccion,nombre_estacion)
		
		G = generateGraph(data,REDUCCION_CAPACIDAD_TRASNOCHE)
		
		flowDict = nx.min_cost_flow(G)

		vagones_totales(flowDict, data, G)
		
		costo_minimo(flowDict,G)

		printGraph(G,data,flowDict)
	
		costo = getFlowCost(flowDict, G)

		print(f"Costo total: {costo}")
  
	else: 
		REDUCCION_CAPACIDAD_TRASNOCHE = (0,"0Station")
		G = generateGraph(data,REDUCCION_CAPACIDAD_TRASNOCHE)
		
		flowDict = nx.min_cost_flow(G)

		vagones_totales(flowDict, data, G)
		
		costo_minimo(flowDict,G)

		printGraph(G,data,flowDict)
	
		costo = getFlowCost(flowDict, G)

		print(f"Costo total: {costo}")
  
	## Experimentacion
	if False:
		rango_tiempo = 6
		for i in range(rango_tiempo):
			data = generate_random_json(num_services=8, num_stations=2,seed=42)
			REDUCCION_CAPACIDAD_TRASNOCHE = (0,"0Station")
			G = generateGraph(data,REDUCCION_CAPACIDAD_TRASNOCHE)
			
			flowDict = nx.min_cost_flow(G)

			vagones_totales(flowDict, data, G)
		
			costo_total = getFlowCost(flowDict, G)

			print(f"Costo total: {costo}")
   
   #### guido viejo 
   
	instance = 2
	if(instance == 0):
		filename = "instances/toy_instance.json"
	elif(instance == 1):
		filename = "instances/instance_2.json"
	else:
		filename = "instances/retiro-tigre-semana.json"

	REDUCCION_CAPACIDAD_TRASNOCHE = (0,"0Station")

	data = getDatafromPath(filename)

	# data = generate_random_json(num_services=4, num_stations=2,seed=42)

	G = generateGraph(data,REDUCCION_CAPACIDAD_TRASNOCHE)
	
	flowDict = nx.min_cost_flow(G)

	# printGraph(G,data,flowDict)

	vagones_totales(flowDict, data, G)
	
	costo_minimo(flowDict,G)

	# printGraph(G,data,flowDict)

	costo = getFlowCost(flowDict, G)

	print(f"Costo total: {costo}")



if __name__ == "__main__":
	main()