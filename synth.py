import z3
import lark


GRAMMAR = """
?start: sum
  | sum "?" sum ":" sum -> if

?sum: term
  | sum "+" term        -> add
  | sum "-" term        -> sub

?term: item
  | term "*"  item      -> mul
  | term "/"  item      -> div
  | term ">>" item      -> shr
  | term "<<" item      -> shl
  | term "^" item      -> pow

?item: NUMBER           -> num
  | "-" item            -> neg
  | CNAME               -> var
  | "(" start ")"

%import common.NUMBER
%import common.WS
%import common.CNAME
%ignore WS
""".strip()

parser = lark.Lark(GRAMMAR)

def z3_expr(tree, vars=None):
    """Create a Z3 expression from a tree.
    Return the Z3 expression and a dict mapping variable names to all
    free variables occurring in the expression. All variables are
    represented as BitVecs of width 8. Optionally, `vars` can be an
    initial set of variables.
    """

    vars = dict(vars) if vars else {}

    # Lazily construct a mapping from names to variables.
    def get_var(name):
        if name in vars:
            return vars[name]
        else:
            v = z3.BitVec(name, 8)
            vars[name] = v
            return v

    return interp(tree, get_var), vars

def interp(tree, lookup):
    op = tree.data
    if op in ('add', 'sub', 'mul', 'div', 'shl', 'shr','pow'):
        lhs = interp(tree.children[0], lookup)
        rhs = interp(tree.children[1], lookup)
        if op == 'add':
            return lhs + rhs
        elif op == 'sub':
            return lhs - rhs
        elif op == 'mul':
            return lhs * rhs
        elif op == 'div':
            return lhs / rhs
        elif op == 'shl':
            return lhs << rhs
        elif op == 'shr':
            return lhs >> rhs
        elif op == 'pow':
            x= rhs;
            temp=lhs;
            if x==0: 
            	return 1;
            while x > 1:
            	temp=temp*lhs;
            	x=x-1;
            return temp
    elif op == 'neg':
        sub = interp(tree.children[0], lookup)
        return -sub
    elif op == 'num':
        return int(tree.children[0])
    elif op == 'var':
        return lookup(tree.children[0])
    elif op == 'if':
	    cond = interp(tree.children[0], lookup)
	    true = interp(tree.children[1], lookup)
	    false = interp(tree.children[2], lookup)
	    return (cond != 0) * true + (cond == 0) * false
        
def solve(phi):
	s=z3.Solver();
	s.add(phi);
	s.check();
	return s.model()
	
	
if __name__== '__main__' :
	#x=z3.BitVec('x',8);
	#slow_expr =x*2
	
	#h=z3.BitVec('h',8);
	#fast_expr = x<<h
	#Example 1
	tree1 = parser.parse("(x ^ 4)+((2*x)^2)+x^(x^0+1)")
	tree2 = parser.parse("(hA * ((hb1 ? x:y) ^2))+ (hB * ((hb2 ? x:y) ^4))")
	#Example 2
	#tree1 = parser.parse("(x ^ 2)+((2*x)^2)+ ((5*y) ^ 2)")
	#tree2 = parser.parse("(hA * ((hb1 ? x:y) ^2))+ (hB * ((hb2 ? x:y) ^2))")
	
	expr1, vars1 = z3_expr(tree1)
	expr2, vars2 = z3_expr(tree2, vars1)
	
	plain_vars = {k: v for k, v in vars1.items()
              if not k.startswith('h')}
	
	goal = z3.ForAll(
	    list(plain_vars.values()),  # For every valuation of variables...
	    expr1 == expr2,  # ...the two expressions produce equal results.
	)
	print(solve(goal))
