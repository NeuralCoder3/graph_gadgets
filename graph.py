from z3 import *
import time
import sys
import functools

s = Solver()

k = 3
n = 30
c = 6 # antenna

# w.l.o.g. 1 .. c are attachment points and 0,1 2,3 ... are paired
assert c % 2 == 0

if len(sys.argv) > 1:
    n = int(sys.argv[1])
if len(sys.argv) > 2:
    c = int(sys.argv[2])

# Create a 2D array of boolean variables
# x[i][j] is true if there is an edge from i to j
x = [ [ Bool("x_%s_%s" % (i+1, j+1)) for j in range(n) ] for i in range(n) ]

# No node has an edge to itself
for px in range(n):
    s.add( Not(x[px][px]) )
    
# undirected graph => x[i][j] == x[j][i]
for px in range(n):
    for py in range(n):
        s.add( x[px][py] == x[py][px] )
    
# k regular => each node has exactly k outgoing edges
for px in range(n):
    count = Sum([ If(x[px][j], 1, 0) for j in range(n) ])
    if px < c:
        s.add( count == k-1 )
    else:
        s.add( count == k )
    
def flatten(xxs):
    return functools.reduce(lambda x,y: x+y, xxs)

def is_isomorph(adj, swaps, name):
    constr = []
    perm = [ [ Bool("%s_%s_%s" % (name, i+1, j+1)) for j in range(n) ] for i in range(n) ]
    for i in range(n):
        constr.append( Sum([ If(perm[i][j], 1, 0) for j in range(n) ]) == 1 )
        constr.append( Sum([ If(perm[j][i], 1, 0) for j in range(n) ]) == 1 )
    swap_nodes = set()
    for s1,s2 in swaps:
        constr.append( perm[s1][s2] )
        constr.append( perm[s2][s1] )
        swap_nodes.add(s1)
        swap_nodes.add(s2)
        
    for a in range(c):
        if a not in swap_nodes:
            constr.append( perm[a][a] )
    
    # Perm x A x Perm
    # intuitively: 
    # A' = Perm x A 
    # if i permuted to l (perm) and l connected to j (adj) 
    # then l connected to j in intermediate matrix
    # A'' = A' x Perm
    # if i connected to l in intermediate matrix and l permuted to j
    # then i connected to j in final matrix
    
    adj_matr = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(
                Or(
                    [
                    And(perm[i][l], adj[l][j])
                    for l in range(n)]
                )
            )
        adj_matr.append( row )
        
    adj_matr2 = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(
                Or(
                    [
                    And(adj_matr[i][l], perm[l][j])
                    for l in range(n)]
                )
            )
        adj_matr2.append( row )
    
    constr.append( And([ adj_matr2[i][j] == adj[i][j] for i in range(n) for j in range(n) ]))
    # return And(constr) # if just positive search is needed
    return Exists(flatten(perm), And(constr))

    
pairs = [ (i, i+1) for i in range(0, c, 2) ]
for pi1, p1 in enumerate(pairs):
    for pi2, p2 in enumerate(pairs):
        if pi2 <= pi1:
            continue
        px, py = p1
        i2, j2 = p2
        p1_str = f"{px}-{py}"
        p2_str = f"{i2}-{j2}"
        print(f"Adding constraints for {p1_str} and {p2_str}")
        s.add( is_isomorph(x, [p1,p2], f"{p1_str}_{p2_str}") )
        
        
for px,py in pairs:
    print(f"Adding negative constraints for {px}-{py}")
    s.add(Not(is_isomorph(x, [(px, py)], f"{px}-{py}")))
        
        
def renderGraph(graph, filename):
    from graphviz import Digraph
    g = Digraph()
    for px in range(n):
        g.node(str(px))

    # draw undirected edges
    for px in range(n):
        for py in range(px+1, n):
            if graph[px][py]:
                g.edge(str(px), str(py), dir="none")
                
    # add antennas
    for px in range(c):
        g.node("A"+str(px), color="red", style="filled")
        
    for px in range(c):
        g.edge("A"+str(px), str(px), color="red", dir="none")
                
    g.render(filename, format="png", cleanup=True)
    
    # write adjacency matrix to file
    with open(f"{filename}.adj", "w") as f:
        for i in range(n):
            for j in range(n):
                f.write("1" if graph[i][j] else "0")
            f.write("\n")
    
with open(f"graph_k{k}_n{n}_c{c}.smt2", "w") as f:
    f.write(s.to_smt2())
    
# from common import export_sat
# export_sat(s, f"graph_k{k}_n{n}_c{c}")
        
count = 0
outfolder = f"graphs_k{k}_n{n}_c{c}"
accept_outfolder = f"gadget_graphs"
if not os.path.exists(outfolder):
    os.makedirs(outfolder)
if not os.path.exists(accept_outfolder):
    os.makedirs(accept_outfolder)
print("Solving...")
while True:
    t0 = time.time()
    res = s.check()
    t1 = time.time()
    if res != sat:
        print(f"No more solutions found after {count} solutions")
        break
    count += 1
    print(f"Solution {count} after {t1-t0:.2f} seconds")
    
    m = s.model()
    r = [ [ m.evaluate(x[i][j]) for j in range(n) ] for i in range(n) ]
    
    s.add( Or([ x[i][j] != r[i][j] for i in range(n) for j in range(n) ]) )
    
    renderGraph(r, f"{outfolder}/{count}")