from math import log
import numpy as np
from igraph import Graph
import time
# from write_graph import *


class GraphSegment:
    def __init__(self, g, nodesInPartS, nodesInPartD, part):
        self.g = g
        self.nodesInPartS = nodesInPartS
        self.nodesInPartD = nodesInPartD
        self.part = part
        self.segments = 1


def graphScope(segment, newSegment):
    encodingCostSegment = totalCostForSegment(segment, segment.segments)

    encodingCostNewGraph = totalCostForSegment(newSegment, newSegment.segments)

    unionGraph = Graph.Bipartite(
        segment.g.vs["type"], segment.g.get_edgelist(), directed=False)
    unionGraph.add_edges(newSegment.g.get_edgelist())
    resultUnion = partitionGraph(unionGraph, 1, segment.segments + 1)
    unionSegment = GraphSegment(
        unionGraph, resultUnion[0], resultUnion[1], resultUnion[2])
    encodingCostUnion = totalCostForSegment(unionSegment, segment.segments + 1)
    print("encodingCostUnion", encodingCostUnion)
    print("encodingCostSegment", encodingCostSegment)
    print("encodingCostNewGraph", encodingCostNewGraph)
    if encodingCostUnion - encodingCostSegment < encodingCostNewGraph:
        unionSegment.segments = segment.segments + 1
        return [unionSegment]
    else:
        return [segment, newSegment]
    print("time.graphScope after: %f " % time.time())


def entropy(arr):
    entropy = 0
    totalInstances = sum(arr)
    for instance in arr:
        if instance > 0:
            entropy += (float(instance) / totalInstances) * \
                log(float(instance) / totalInstances, 2)
    return -entropy


def crossEntropy(arrP, arrQ):
    entropy = 0
    totalInstancesP = sum(arrP)
    totalInstancesQ = sum(arrQ)
    for i in range(len(arrP)):
        if arrP[i] > 0:
            if (arrQ[i] == 0):
                print(arrP)
                print(arrQ)
            entropy += (float(arrP[i]) / totalInstancesP) * \
                log(float(arrQ[i]) / totalInstancesQ, 2)
    return -entropy


def totalCost(g, nodesInPartS, nodesInPartD, part, sourceNodes, numberOfSegments=1):
    # source and destination are arrays of frequencies for partitions
    partitionToPartition = createPartitionToPartition(
        g, nodesInPartS, nodesInPartD, part, sourceNodes, numberOfSegments)

    source = [len(elem) for elem in nodesInPartS]
    destination = [len(elem) for elem in nodesInPartD]
    m = sum(source)
    n = sum(destination)
    partitionEncodingCost = m * entropy(source) + n * entropy(destination)
    graphEncodingCost = len(g.es)
    k = len(source)
    l = len(destination)
    for i in range(k):
        for j in range(l):
            gamma = source[i] * destination[j] * numberOfSegments
            arr = []
            arr.append(partitionToPartition[i].tolist()[0][j])
            arr.append(gamma - arr[0])
            graphEncodingCost += gamma * entropy(arr)
    return partitionEncodingCost + graphEncodingCost


def totalCostForSegment(segment, numberOfSegments):
    sourceNodes = [i for i, x in enumerate(segment.g.vs["type"]) if x == False]
    return totalCost(segment.g, segment.nodesInPartS, segment.nodesInPartD, segment.part, sourceNodes, numberOfSegments)


def averageEntropy(g, nodesInPartS, nodesInPartD, part, partIndex, sourceNodes, numberOfSegments):
    partEntropy = 0
    destNodesCount = len(g.vs) - len(sourceNodes)
    for node in nodesInPartS[partIndex]:
        arr = [0] * len(nodesInPartD)
        for neighbor in g.neighbors(node):
            arr[part[neighbor]] += 1
        arr.append(destNodesCount * numberOfSegments - sum(arr))
        partEntropy += entropy(arr)
    return partEntropy / len(nodesInPartS)


def findPartitionToSplit(g, nodesInPartS, nodesInPartD, part, sourceNodes, numberOfSegments):
    maxEntropy = 0
    maxPartition = 0
    for partIndex in range(len(nodesInPartS)):
        avgEntropy = averageEntropy(
            g, nodesInPartS, nodesInPartD, part, partIndex, sourceNodes, numberOfSegments)
    # print("average entropy for partition", partIndex, "=", avgEntropy)
    if avgEntropy > maxEntropy:
        maxEntropy = avgEntropy
        maxPartition = partIndex
    return maxPartition


def reGroup(g, nodesInPartS, nodesInPartD, part, sourceNodes, numberOfSegments):
    sourceNodesCount = len(sourceNodes)
    destNodesCount = len(g.vs) - len(sourceNodes)
    partitionToPartition = np.zeros(
        shape=(len(nodesInPartS), len(nodesInPartD)))
    nodeToPartition = np.zeros(shape=(sourceNodesCount, len(nodesInPartD)))
    for node in range(sourceNodesCount):
        for neighbor in g.neighbors(sourceNodes[node]):
            nodeToPartition[node][part[neighbor]] += 1
            partitionToPartition[part[sourceNodes[node]]][part[neighbor]] += 1
    complementaryColumnForNodes = destNodesCount * numberOfSegments - \
        np.apply_along_axis(sum, axis=1, arr=nodeToPartition)
    nodeToPartition = np.append(nodeToPartition, np.transpose(
        np.matrix(complementaryColumnForNodes)), axis=1)
    possibleEdgesFromPartitions = np.array(
        [len(elem) for elem in nodesInPartS]) * destNodesCount * numberOfSegments

    existingEdgesFromPartitions = np.apply_along_axis(
        sum, axis=1, arr=partitionToPartition)
    complementaryColumnForPartitions = possibleEdgesFromPartitions - \
        existingEdgesFromPartitions
    partitionToPartition = np.append(partitionToPartition, np.transpose(
        np.matrix(complementaryColumnForPartitions)), axis=1)
    for sourceIndex in range(sourceNodesCount):
        bestPartitionCost = 1000000
        for partition in range(len(nodesInPartS)):
            if (partition == part[sourceNodes[sourceIndex]]):
                currentCrossEntropy = crossEntropy(nodeToPartition[sourceIndex].tolist()[
                                                   0], partitionToPartition[partition].tolist()[0])
            else:
                currentCrossEntropy = crossEntropy(nodeToPartition[sourceIndex].tolist(
                )[0], (partitionToPartition[partition] + nodeToPartition[sourceIndex]).tolist()[0])
    # print("node:", sourceNodes[sourceIndex], ", partition:", partition, ", cost:", currentCrossEntropy)
        if currentCrossEntropy < bestPartitionCost:
            bestPartition = partition
            bestPartitionCost = currentCrossEntropy
        previousPartition = part[sourceNodes[sourceIndex]]
        nodesInPartS[previousPartition].remove(sourceNodes[sourceIndex])
        nodesInPartS[bestPartition].append(sourceNodes[sourceIndex])
        partitionToPartition[previousPartition] = partitionToPartition[previousPartition] - \
            nodeToPartition[sourceIndex]
        partitionToPartition[bestPartition] = partitionToPartition[bestPartition] + \
            nodeToPartition[sourceIndex]
        part[sourceNodes[sourceIndex]] = bestPartition
        if len(nodesInPartS[previousPartition]) == 0:
            del nodesInPartS[previousPartition]
            partitionToPartition = np.delete(
                partitionToPartition, (previousPartition), axis=0)
            for sourceNode in sourceNodes:
                if part[sourceNode] > previousPartition:
                    part[sourceNode] -= 1


def searchKL(g, nodesInPartS, nodesInPartD, part, sourceNodes, numberOfSegments, verbose=False):
    partIndex = findPartitionToSplit(
        g, nodesInPartS, nodesInPartD, part, sourceNodes, numberOfSegments)
    if len(nodesInPartS[partIndex]) > 1:
        currentAverageEntropy = averageEntropy(
            g, nodesInPartS, nodesInPartD, part, partIndex, sourceNodes, numberOfSegments)
        #       print("current average entropy", currentAverageEntropy)
        for s in nodesInPartS[partIndex]:
            newNodesInPartS = nodesInPartS[:]
            newNodesInPartS[partIndex].remove(s)
            newNodesInPartS.append([s])
            newPart = part[:]
            newPart[s] = len(nodesInPartS)
            newAverageEntropy = averageEntropy(
                g, newNodesInPartS, nodesInPartD, newPart, partIndex, sourceNodes, numberOfSegments)
        #           print("new average entropy", newAverageEntropy)
            if newAverageEntropy < currentAverageEntropy:
                nodesInPartS = newNodesInPartS
                currentAverageEntropy = newAverageEntropy
                part = newPart
        if (verbose):
            print("after split:", nodesInPartS)
        reGroup(g, nodesInPartS, nodesInPartD,
                part, sourceNodes, numberOfSegments)
        if (verbose):
            print("after update:", nodesInPartS)
    currentTotalCost = totalCost(
        g, nodesInPartS, nodesInPartD, part, sourceNodes)
    #   print("current total cost:", currentTotalCost)
    k = len(nodesInPartS)
    i = 0
    while i < k-1:
        j = i+1
        while j < k:
            newNodesInPartS = []
            for partition in range(len(nodesInPartS)):
                newNodesInPartS.append(nodesInPartS[partition][:])
            newNodesInPartS[i].extend(newNodesInPartS[j])
            del newNodesInPartS[j]
            newPart = part[:]
            for sourceNode in sourceNodes:
                if newPart[sourceNode] == j:
                    newPart[sourceNode] = i
                elif newPart[sourceNode] > j:
                    newPart[sourceNode] -= 1
            newTotalCost = totalCost(
                g, newNodesInPartS, nodesInPartD, newPart, sourceNodes)
    #           print("new total cost:", newTotalCost, "source:", nodesInPartS)
            if newTotalCost <= currentTotalCost:
                nodesInPartS = newNodesInPartS
                part = newPart
                currentTotalCost = newTotalCost
                k -= 1
            else:
                j += 1
        i += 1
    if (verbose):
        print("after merge:", nodesInPartS)
    return [nodesInPartS, part]


def createPartitionToPartition(g, nodesInPartS, nodesInPartD, part, sourceNodes, numberOfSegments):
    partitionToPartition = np.zeros(
        shape=(len(nodesInPartS), len(nodesInPartD)))
    for nodeIndex in range(len(sourceNodes)):
        for neighbor in g.neighbors(sourceNodes[nodeIndex]):
            partitionToPartition[part[sourceNodes[nodeIndex]]
                                 ][part[neighbor]] += 1
    destNodesCount = len(g.vs) - len(sourceNodes)
    possibleEdgesFromPartitions = np.array(
        [len(elem) for elem in nodesInPartS]) * destNodesCount * numberOfSegments
    existingEdgesFromPartitions = np.apply_along_axis(
        sum, axis=1, arr=partitionToPartition)
    complementaryColumnForPartitions = possibleEdgesFromPartitions - \
        existingEdgesFromPartitions
    partitionToPartition = np.append(partitionToPartition, np.transpose(
        np.matrix(complementaryColumnForPartitions)), axis=1)
    return partitionToPartition


def initializeDestPartition(destNodes, part):
    destNodePartition = 0
    nodesInPartD = []
    for destNode in destNodes:
        nodesInPartD.append([destNode])
        part[destNode] = destNodePartition
        destNodePartition += 1
    return [part, nodesInPartD]


def partitionGraph(g, iterations, numberOfSegments=1):
    totalNodes = len(g.vs)
    part = [0] * totalNodes
    nodesInPartS = []
    nodesInPartD = []
    sourceNodes = [i for i, x in enumerate(g.vs["type"]) if x == False]
    destNodes = [i for i, x in enumerate(g.vs["type"]) if x == True]
    nodesInPartS.append(sourceNodes[:])
    nodesInPartD.append(destNodes[:])

    # initialize destPartition so that each node is in its own partition
    #     initialized = initializeDestPartition(destNodes, part)
    #     part = initialized[0]
    #     nodesInPartD = initialized[1]
    for i in range(iterations):
        print("iteration", i, ":")
        # searchKL for source nodes
        result = searchKL(g, nodesInPartS, nodesInPartD,
                          part, sourceNodes, numberOfSegments)
        nodesInPartS = result[0]
        part = result[1]
        if (i == 0):
            nodesInPartD = [destNodes[:]]
            for destNode in destNodes:
                part[destNode] = 0

        # searchKL for dest nodes
        result = searchKL(g, nodesInPartD, nodesInPartS,
                          part, destNodes, numberOfSegments)
        nodesInPartD = result[0]
        part = result[1]
        print("source:", nodesInPartS, "\n dest:",
              nodesInPartD, "\n partitioning", part, "\n")

        adj = g.get_adjacency()
        # writeMatrixToPnms(adj, 'output/initial_matrix_wo.pnm', 'output/partitioned_noise_wo_iter_' +
        #                   str(i) + '.pnm', sourceNodes, destNodes, nodesInPartS, nodesInPartD)
        # writeInitialGraphToFile(
        #     adj, sourceNodes, destNodes, 'output/initial_matrix_noise_wo.txt')
        # writePartitionedGraphToFile(nodesInPartS, nodesInPartD, part, adj, sourceNodes,
        #                             destNodes, 'output/partitioned_noise_wo_iter_' + str(i) + '.txt')

    return [nodesInPartS, nodesInPartD, part]

# def segmentGraphToPartitions(segment, newGraph):
#
