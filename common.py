from z3 import *

def z3_to_cnf_clauses(formula):
    """Convert a Z3 formula into a list of CNF clauses."""
    # Tactic to convert the formula to CNF
    goal = Goal()
    goal.add(formula)
    cnf = Then(Tactic('tseitin-cnf'), Tactic('simplify')).apply(goal)
    assert len(cnf) == 1, "Expected a single goal"
    clauses = []
    for clause in cnf[0]:
        # Collect literals for each clause
        literals = []
        if is_or(clause):
            for literal in clause.children():
                literals.append(literal)
        else:
            literals.append(clause)
        clauses.append(literals)
    return clauses

def write_dimacs(clauses, var_mapping, filename="formula.dimacs"):
    """Write clauses to a DIMACS file."""
    with open(filename, 'w') as f:
        # DIMACS header
        num_vars = len(var_mapping)
        num_clauses = len(clauses)
        f.write(f"p cnf {num_vars} {num_clauses}\n")
        
        # Write each clause in DIMACS format
        for clause in clauses:
            clause_str = ""
            for literal in clause:
                var = literal.decl().name()
                if var == 'not':
                    var = literal.children()[0].decl().name()
                    var_id = -var_mapping[var]
                else:
                    var_id = var_mapping[var]
                clause_str += f"{var_id} "
            clause_str += "0\n"
            f.write(clause_str)

def export_sat(s, filename):
    # Get CNF clauses from the formula
    clauses = z3_to_cnf_clauses(And(s.assertions()))
    # Create a mapping from Z3 variables to integers
    var_mapping = {str(v): i+1 for i, v in enumerate(set(literal.decl() for clause in clauses for literal in clause))}
    # Write the DIMACS file
    write_dimacs(clauses, var_mapping, filename+".dimacs" )
    # save var mapping to file
    with open(filename+".var_mapping", "w") as f:
        for var, i in var_mapping.items():
            f.write(f"{var} {i}\n")
