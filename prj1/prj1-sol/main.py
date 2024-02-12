
import re, json, sys
from collections import namedtuple

# Define token types
TOKEN_INTEGER = 'INTEGER'
TOKEN_ATOM = 'ATOM'
TOKEN_KEY = 'KEY'
TOKEN_VALUE = 'VALUE'
TOKEN_BOOLEAN = 'BOOLEAN'
TOKEN_LEFT_SQUARE_BRACKET = 'LEFT_SQUARE_BRACKET'
TOKEN_RIGHT_SQUARE_BRACKET = 'RIGHT_SQUARE_BRACKET'
TOKEN_LEFT_CURLY_BRACE = 'LEFT_CURLY_BRACE'
TOKEN_RIGHT_CURLY_BRACE = 'RIGHT_CURLY_BRACE'
TOKEN_PERCENT_LEFT_CURLY_BRACE = 'PERCENT_LEFT_CURLY_BRACE'
TOKEN_COMMA = 'COMMA'
TOKEN_RIGHT_ARROW = 'RIGHT_ARROW'
TOKEN_UNDERSCORE = 'UNDERSCORE'
TOKEN_COLON = 'COLON'
TOKEN_TRUE = 'TRUE'
TOKEN_FALSE = 'FALSE'
TOKEN_EMPTY_SPACE = 'EMPTY_SPACE'
TOKEN_EOF = 'EOF'

# Token regular expressions
TOKEN_REGEX = [
    (TOKEN_INTEGER, r'\d+(_\d+)*'),
    (TOKEN_ATOM, r':[a-zA-Z_][a-zA-Z0-9_]*'),
    (TOKEN_COMMA, r','),
    (TOKEN_COLON, r':'),
    (TOKEN_KEY, r'[a-zA-Z_][a-zA-Z0-9_]*:'),
    (TOKEN_VALUE, r'''(['"])(.*?)\d+(_\d+)*\1'''),
    (TOKEN_BOOLEAN, r'true|false'),
    (TOKEN_LEFT_SQUARE_BRACKET, r'\['),
    (TOKEN_RIGHT_SQUARE_BRACKET, r'\]'),
    (TOKEN_LEFT_CURLY_BRACE, r'\{'),
    (TOKEN_RIGHT_CURLY_BRACE, r'\}'),
    (TOKEN_PERCENT_LEFT_CURLY_BRACE, r'%\{'),
    (TOKEN_RIGHT_ARROW, r'=>'),
    (TOKEN_UNDERSCORE, r'_'),
    (TOKEN_EMPTY_SPACE, r'( |\t)*'),
    (TOKEN_EOF, r'<EOF>')
]


'''
<language> ::= <sentence>

<sentence> ::= { <data-literal> }

<data-literal> ::= <list-literal> | <tuple-literal> | <map-literal> | <primitive-literal>

<primitive-literal> ::= <integer> | <atom> | <boolean>

<list-literal> ::= "[" [ <data-literal> { "," <data-literal> } ] "]"

<tuple-literal> ::= "{" [ <data-literal> { "," <data-literal> } ] "}"

<map-literal> ::= "%{" [ <key-pair> { "," <key-pair> } ] "}"

<key-pair> ::= <data-literal> "=>" <data-literal> | <key> <data-literal>

<integer> ::= <digit> { <digit> | "_" }

<atom> ::= ":" <alphabetic> { <alphanumeric> | "_" }

<key> ::= <alphabetic> { <alphanumeric> | "_" } ":"

<boolean> ::= "true" | "false"

<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<alphabetic> ::= "a" | "b" | "c" | ... | "z" | "A" | "B" | ... | "Z"

<alphanumeric> ::= <alphabetic> | <digit>

'''



################### AST Node types #########################
class Node:
    def to_dict(self):
        raise NotImplementedError("Subclasses must implement to_dict()")

class LanguageNode(Node):
    def __init__(self, sentence):
        self.sentence = sentence
    def to_dict(self):
        return self.sentence.to_dict()
        # return {"language": self.sentence.to_dict()}

class SentenceNode(Node):
    def __init__(self, data_literals):
        self.data_literals = data_literals
    def to_dict(self):
        return [data_literal.to_dict() for data_literal in self.data_literals if data_literal]
        # return {"sentence": [data_literal.to_dict() for data_literal in self.data_literals if data_literal]}

class DataLiteralNode(Node):
    def __init__(self, value):
        self.value = value
    def to_dict(self):
        return {"DataLiteral": self.value}
        
class KeyNode(DataLiteralNode):
    def __init__(self, key):
        self.key = key
    def to_dict(self):
        return self.key
        
class ValueNode(DataLiteralNode):
    def __init__(self, value):
        self.value = value
    def to_dict(self):
        return self.value

class ListLiteralNode(DataLiteralNode):
    def __init__(self, data_literals):
        self.data_literals = data_literals
    def to_dict(self):
        return {"%k":"list", "%v": [data_literal.to_dict() for data_literal in self.data_literals if data_literal]}
        # return {"list_literal": [data_literal.to_dict() for data_literal in self.data_literals if data_literal]}
    

class TupleLiteralNode(DataLiteralNode):
    def __init__(self, data_literals):
        self.data_literals = data_literals
    def to_dict(self):
        return {"%k":"tuple", "%v": [data_literal.to_dict() for data_literal in self.data_literals if data_literal]}
        # return {"tuple_literal": [data_literal.to_dict() for data_literal in self.data_literals if data_literal]}
    

class MapLiteralNode(DataLiteralNode):
    def __init__(self, key_pairs):
        self.key_pairs = key_pairs
    def to_dict(self):
        return {"%k":"map", "%v": [key_pair.to_dict() for key_pair in self.key_pairs if key_pair]}
        # return {"map_literal": [key_pair.to_dict() for key_pair in self.key_pairs if key_pair]}
    

class PrimitiveLiteralNode(DataLiteralNode):
    def __init__(self, value):
        self.value = value
    def to_dict(self):
        return {"primitive": self.value}

class IntegerNode(PrimitiveLiteralNode):
    def __init__(self, value):
        self.value = value
    def to_dict(self):
        return {"%k":"int", "%v": int(self.value)}
        # return {"integer": self.value}

class AtomNode(PrimitiveLiteralNode):
    def __init__(self, value):
        self.value = value
    def to_dict(self):
        return {"%k": "atom", "%v": self.value}
        # return {"atom": self.value}

class KeyNode(PrimitiveLiteralNode):
    def __init__(self, value):
        self.value = value
    def to_dict(self):
        return {"%k":"atom", "%v": self.value[-1::-1]}
        # return {"key": self.value}

class BooleanNode(PrimitiveLiteralNode):
    def __init__(self, value):
        self.value = value
    def to_dict(self):
        if(self.value == "true"): return {"%k":"bool", "%v": True}
        else: return {"%k":"bool", "%v": False}
        # print(self.value)
        # return {"bool": self.value}

class KeyPairNode(Node):
    def __init__(self, key, value):
        self.key = key
        self.value = value
    def to_dict(self):
        return [self.key.to_dict(), self.value.to_dict()]
        # return {"key_pair": {"%k": self.key.to_dict(), "%v": self.value.to_dict()}}
        
        
        

####################### Parser ##########################
def parse(tokens):
    def match_token(token_type):
        nonlocal tokens
        if tokens and tokens[0][0] == token_type:
            return tokens.pop(0)
        # sys.exit(1)
        return None

    def sentence():
        data_literals = []
        while tokens and any([True for token_kind,regex in TOKEN_REGEX if tokens[0][0] == token_kind]):
            data_literals.append(data_literal())
        return SentenceNode(data_literals)

    def data_literal():
        try: 
            token = match_token(TOKEN_LEFT_SQUARE_BRACKET)
            if token:
                return list_literal()
            token = match_token(TOKEN_LEFT_CURLY_BRACE)
            if token:
                return tuple_literal()
            token = match_token(TOKEN_PERCENT_LEFT_CURLY_BRACE)
            if token:
                return map_literal()
            token = match_token(TOKEN_COLON)
            if token:
                return colon_literal()
            token = match_token(TOKEN_RIGHT_ARROW)
            if token:
                return right_arrow_literal()
            token = match_token(TOKEN_ATOM)
            if token:
                return AtomNode(token[1])
            token = match_token(TOKEN_KEY)
            if token:
                return KeyNode(token[1])
            token = match_token(TOKEN_VALUE)
            if token:
                return ValueNode(token[1])
            token = match_token(TOKEN_EOF)
            if token:
                return eof_literal()
            # token = match_token(TOKEN_EMPTY_SPACE)
            # if token:
            #     return empty_space()
            token = match_token(TOKEN_INTEGER)
            if token:
                return IntegerNode(token[1])
            token = match_token(TOKEN_BOOLEAN)
            if token:
                return BooleanNode(token[1])
            raise ValueError(f"Unexpected token: {tokens[0]}")
        except:
            print("Unexpected token error")
            sys.exit(1)
        
    def empty_space():
        match_token(empty_space)
        
    def eof_literal():
        match_token(TOKEN_EOF)
        
    def colon_literal():
        match_token(TOKEN_COLON)
        
    def key_literal():
        match_token(TOKEN_KEY)
        
    def value_literal():
        match_token(TOKEN_VALUE)
        
    def right_arrow_literal():
        match_token(TOKEN_RIGHT_ARROW)

    def list_literal():
        data_literals = []
        match_token(TOKEN_LEFT_SQUARE_BRACKET)
        while tokens and tokens[0][0] != TOKEN_RIGHT_SQUARE_BRACKET:
            # print(tokens)
            data_literals.append(data_literal())
            if tokens and tokens[0][0] == TOKEN_COMMA:
                match_token(TOKEN_COMMA)
                if(tokens[0][0] == TOKEN_RIGHT_SQUARE_BRACKET):
                    sys.exit(1)
        if(match_token(TOKEN_RIGHT_SQUARE_BRACKET) == None):
            sys.exit(1)
        return ListLiteralNode(data_literals)

    def tuple_literal():
        data_literals = []
        match_token(TOKEN_LEFT_CURLY_BRACE)
        while tokens and tokens[0][0] != TOKEN_RIGHT_CURLY_BRACE:
            data_literals.append(data_literal())
            if tokens and tokens[0][0] == TOKEN_COMMA:
                match_token(TOKEN_COMMA)
                if(tokens[0][0] == TOKEN_RIGHT_CURLY_BRACE):
                    sys.exit(1)
        if(match_token(TOKEN_RIGHT_CURLY_BRACE)==None):
            sys.exit(1)
        return TupleLiteralNode(data_literals)

    def map_literal():
        key_pairs = []
        match_token(TOKEN_PERCENT_LEFT_CURLY_BRACE)
        while tokens and tokens[0][0] != TOKEN_RIGHT_CURLY_BRACE:
            key_pairs.append(key_pair())
            if tokens and tokens[0][0] == TOKEN_COMMA:
                match_token(TOKEN_COMMA)
                if(tokens[0][0] == TOKEN_RIGHT_CURLY_BRACE):
                    sys.exit(1)
        if(match_token(TOKEN_RIGHT_CURLY_BRACE) == None):
            sys.exit(1)
        return MapLiteralNode(key_pairs)

    def key_pair():
        try: 
            key = data_literal()
            # print(key)
            if tokens and tokens[0][0] == TOKEN_RIGHT_ARROW:
                match_token(TOKEN_RIGHT_ARROW)
                value = data_literal()
                return KeyPairNode(key, value)
            elif tokens and tokens[0][0] == TOKEN_COLON:
                match_token(TOKEN_COLON)
                value = data_literal()
                return KeyPairNode(key, value)
            elif tokens:
                value = data_literal()
                return KeyPairNode(key, value)
            else:
                raise ValueError(f"Invalid key-pair: {tokens[0]}")
        except:
            print("In valid key-pair")
            sys.exit(1)

    root_node = LanguageNode(sentence())
    return root_node


########################## Parser 2 ##########################



########################### Lexer ############################
SKIP_RE = re.compile(r'(( |\t|\n)|\#.*)+')

def tokenize(input_str):
    tokens = []
    pos = 0
    
    try:
        while pos < len(input_str):
            match = None
            match = SKIP_RE.match(input_str, pos)
            if match:
                pos += len(match.group())
            if pos >= len(input_str): 
                break
            
            for token_kind, regex_pattern in TOKEN_REGEX:
                regex = re.compile(regex_pattern)
                match = regex.match(input_str, pos)
                if match:
                    lexeme = match.group(0)
                    # pos = match.end()
                    pos+=len(lexeme)
                    # print(match, lexeme, pos, len(lexeme))
                    tokens.append(Token(token_kind, lexeme, pos))
                    # print(input_str[pos])
                    # if(input_str[pos] != " " or input_str[pos] != "\n" 
                    #    or input_str[pos] != ","): 
                    #     sys.exit(1)
                    break
            # print(tokens)
            if not match: 
                raise ValueError(f"Invalid token at position {pos}: {input_str[pos:]}")
    except:
        print(f"Invalid token at position {pos}")
        sys.exit(1)
        
    tokens.append(Token('EOF', '<EOF>', pos+1))
    return tokens



#################### Run Test cases #################################3
def run_tests():
    test_input_list = [
        "", 
        "[]",
        "# this file contains no data", 
        "# this file contains no data \n #but it contains multiple comments",
        "# single atom\n:atom",
        # "[1,true,{:key=>'value',:key2=>55,key3:'value3'},%{:key=>'value',key3:'value3'}]",
        "# single int \n 1234",
        "# multiple int's with internal underscores \n 123_456_789 \n 1_2_3"
        "false\ntrue\ntrue false",
        "true false",
        "12_34\ntrue\n:some_long_atom_1234\nfalse\n833_4",
        "[]\n[\n]",
        "[ :a, 22, :b ][]\n[\n:some_atom12,\n# 99\n12\n]"
        "{}\n{\n}",
        "{ :a, 22 }\n{:x, :y, :z}{}\n{\n33\n} #{55}",
        "%{}\n%{\n#:ignored\n}"
        "%{ a: 22, :b => 33 }\n%{ [22] => 33, {:x} => :x } %{}\n%{ 22 => # ignore\n33\n}",
        "%{ [:a, 22] => { [1, 2, 3], :x },\nx: [99, %{ a: 33 }]\n}\n{ [1, 2], {:a, 22}, %{ a: 99, :b => 11} }\n[ {1, 2}, %{[:x] => 33, b: 44}, :c, [], [:d, 55] ]",                          
        "[1, 2",
        "%{ a: 33",
        "truefalse",
        "[1,]",
        "{}}",
        "12_3_"
    ]
    
    i=0
    for s in test_input_list :
        print("============================== Test Case "+str(i+1)+" ================================")
        print(f"\nInput string: {s}")
        
        tokens = tokenize(s)
        print(f"Tokens: {tokens}")
        
        print("\nJSON:")
        ast = parse(tokens)
        json_output = json.dumps(ast.to_dict(), indent=2)
        print(json_output)
        
        i+=1
   
   
   

########################## driver_code ############################

Token = namedtuple('Token', 'kind lexeme pos')


# input_string = "[1,true,{:key=>'value',:key2=>55,key3:'value3'},%{:key=>'value',key3:'value3'}]"
# input_string = "%{ [:a, 22] => { [1, 2, 3], :x },\nx: [99, %{ a: 33 }]\n}\n{ [1, 2], {:a, 22}, %{ a: 99, :b => 11} }\n[ {1, 2}, %{[:x] => 33, b: 44}, :c, [], [:d, 55] ]"                          
# input_string = "truefalse"
input_string = sys.stdin.read()
# print(f"Input string: {input_string}")

tokens = tokenize(input_string)
# print(*tokens,sep="\n")

ast = parse(tokens)
# print(f"\nAST: {ast}")

json_output = json.dumps(ast.to_dict(), indent=2)
# print("JSON:")
print(json_output)
# print(ast.to_dict())

# print("##################################### Running Tests #####################################")
# run_tests()




