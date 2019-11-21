from igraph import Graph
# from Queue import PriorityQueue
# from write_graph import *
from graphScope import partitionGraph, GraphSegment, graphScope
import time


class Edge:
    def __init__(self, v1, v2, timestamp):
        self.v1 = v1
        self.v2 = v2
        self.timestamp = timestamp

    def __cmp__(self, other):
        return cmp(self.timestamp, other.timestamp)


def readEdges(fileName):
    f = open(fileName, 'r')
    for line in f:
        pieces = line.strip().split(';')
        edges.put(Edge(int(pieces[0]), int(pieces[1]), int(pieces[2])))
        types[int(pieces[0])] = 0
        types[int(pieces[1])] = 1
    f.close()


# start!
types = {}
# edges = PriorityQueue()

readEdges("edgelists/country_dataset_unique.txt")

graphSegments = []

while(not edges.empty()):
    edgesForTimestamp = []
    timestamp = edges.queue[0].timestamp
    print(timestamp)
    while(not edges.empty() and edges.queue[0].timestamp == timestamp):
        edge = edges.get()
        print(edge.timestamp)
        edgesForTimestamp.append((edge.v1, edge.v2))
    print("change")
    g = Graph.Bipartite(types.values(), edgesForTimestamp, directed=False)
    g.vs["label"] = range(len(types))
    graphSegments.append(g)


timestamp = 1
segments = []
for g in graphSegments:
    # print "timestamp", timestamp, "\n"
    result = partitionGraph(g, 1)
    nodesInPartS = result[0]
    nodesInPartD = result[1]
    part = result[2]
    # print "\n"
    segments.append(GraphSegment(g, result[0], result[1], result[2]))
    # # write files
    adj = g.get_adjacency()
    sourceNodes = [i for i, x in enumerate(g.vs["type"]) if x == False]
    destNodes = [i for i, x in enumerate(g.vs["type"]) if x == True]
    # writeMatrixToPnms(adj, 'output/initial_matrix_countries' + str(timestamp) + '.pnm',
    #                   'output/partitioned_countries_timestamp' + str(timestamp) + '.pnm', sourceNodes, destNodes, nodesInPartS, nodesInPartD)
    # writeInitialGraphToFile(adj, sourceNodes, destNodes,
    #                         'output/initial_matrix_countries_timestamp' + str(timestamp) + '.txt')
    # writePartitionedGraphToFile(nodesInPartS, nodesInPartD, part, adj, sourceNodes,
    #                             destNodes, 'output/partitioned_countries_timestamp' + str(timestamp) + '.txt')
    timestamp += 1

j = 0
while j < len(segments) - 1:
    resultSegment = graphScope(segments[j], segments[j+1])
    segments[j:j+2] = resultSegment
    if len(resultSegment) == 2:
        j += 1

segmentNumber = 1
for segment in segments:
    # print "segment number:", segmentNumber, "segment count:", segment.segments
    adj = segment.g.get_adjacency()
    sourceNodes = [i for i, x in enumerate(segment.g.vs["type"]) if x == False]
    destNodes = [i for i, x in enumerate(segment.g.vs["type"]) if x == True]
    # writeMatrixToPnms(adj, 'output/initial_matrix_countries_segment' + str(segmentNumber) + '.pnm', 'output/partitioned_countries_segment' +
    #                   str(segmentNumber) + '.pnm', sourceNodes, destNodes, segment.nodesInPartS, segment.nodesInPartD)
    # writeInitialGraphToFile(adj, sourceNodes, destNodes,
    #                         'output/initial_countries_segment' + str(segmentNumber) + '.txt')
    # writePartitionedGraphToFile(segment.nodesInPartS, segment.nodesInPartD, segment.part, adj,
    #                             sourceNodes, destNodes, 'output/partitioned_countries_segment' + str(segmentNumber) + '.txt')
    segmentNumber += 1
