import json
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random

### Hacer el grafo

def generateGraph(data,modificaciones_trasnoche):
	## Genera el grafo G
	G = nx.DiGraph()

	addNodesAndTrainEdges(data, G)
	addTraspasoEdges(data, G)
	addTrasNocheEdges(data, G,modificaciones_trasnoche)

	return G

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
			G.add_edge(station_nodes[i], station_nodes[i+1], weight=0, capacity=float("inf") ,color='blue')
            

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
		if(modificacion_trasnoche[0] != 0):
			if(modificacion_trasnoche[1] == estacion):
				G.add_edge(final, inicio, weight=1,capacity = data["rs_info"]["max_rs"] - modificacion_trasnoche[0],color='red')
			else:
				G.add_edge(final, inicio, weight=1,capacity = float("inf"),color='red')
		else:
			G.add_edge(final, inicio, weight=1,capacity = float("inf"),color='red')


## imprimir el grafico
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
    
    edges_with_curves = get_curved_edges(G)  # Especificar aristas con curva aquí
    
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
    
    
## Determinar los costos 
def costo_minimo(flowDict,G):
	#arregla la representacion en el grafo
	for u, v in G.edges:
		if G.edges[u,v]['color'] == 'green':
			flowDict[u][v] += G.nodes[u]["demand"] 
            

def vagones_totales(flowDict,data, G):
	#Costo por cada estacion medido en cantidad de vagones necesarios para satisfacer la demanda
	
	flujo_estacion = 0

	for estacion in data["stations"]:
		inicio = getFirstDeparture(estacion, data, G)
		final = getLastArrival(estacion, data, G)
		flujo_estacion = flowDict[final][inicio]
  
		print(F"{estacion}: {flujo_estacion} vagones")
				
					
def getFlowCost(flowDict, G):
	#Costo total para la empresa medidio en unidades de vagones
	cost = 0
	for u,v in G.edges:
		cost += flowDict[u][v] * G.edges[u,v]['weight']
	return cost     


## genera cronograma random 
def generate_random_json(
        num_services=8, 
        num_stations=2, 
        max_time=1440, # 1440 minutos === 60*24 minutos === 1 dia
        demand_value=500, 
        capacity=100, 
        max_rs=25,
        time_beetween_services = 58,
        cost_per_unit = 1.0,
		seed = 42
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


## Funciones auxiliares 
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
 
def experimentacion_1():
	generate_random_json(
			num_services=8, 
			num_stations=2, 
			max_time=1440, # 1440 minutos === 60*24 minutos === 1 dia
			demand_value=500, 
			capacity=100, 
			max_rs=25,
			time_beetween_services = 58,
			cost_per_unit = 1.0,
			seed = 42
			)
 
def main():
    
	
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
  
  
	######################### EXPERIMENTACION #########################

	# Lista de valores de x que queremos probar
	valores_x = range(0, 1000,50)
	resultados = []

	REDUCCION_CAPACIDAD_TRASNOCHE = (0,"0Station")

	for x in valores_x:
		try:
			data = generate_random_json(num_services=4, num_stations=2,demand_value = x,seed=42)
			G = generateGraph(data,REDUCCION_CAPACIDAD_TRASNOCHE)
			flowDict = nx.min_cost_flow(G)
			vagones_totales(flowDict, data, G)
			costo = getFlowCost(flowDict, G)

			resultados.append((x, costo, True))  # El tercer elemento indica que no hubo error
		except Exception as e:
			print(f"Error para x = {x}: {e}")
			resultados.append((x, None, False))  # El tercer elemento indica que hubo error

	# Separar los resultados válidos y los que rompieron
	valores_x_validos = [x for x, res, valid in resultados if valid]
	valores_y_validos = [res for x, res, valid in resultados if valid]

	valores_x_invalidos = [x for x, res, valid in resultados if not valid]
	valores_y_invalidos = [0 for x, res, valid in resultados if not valid]  # Poner en 0 o algún valor placeholder
 
	# Graficar los resultados
	plt.plot(valores_x_validos, valores_y_validos, marker='o', linestyle='-', label='Valores válidos')
	plt.scatter(valores_x_invalidos, valores_y_invalidos, color='red', marker='x', label='Errores')

	# Añadir etiquetas y título
	plt.xlabel('x')
	plt.ylabel('mi_funcion(x)')
	plt.title('Resultados de mi_funcion')
	plt.legend()

	# Mostrar el gráfico
	plt.show()




if __name__ == "__main__":
	main()