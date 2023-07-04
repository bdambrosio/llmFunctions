import demjson3
import json

def ensure_double_quotes(input_string):
    # Parse JavaScript style JSON
    js_data = demjson3.decode(input_string)

    # Dump data as standard JSON
    json_data = json.dumps(js_data)

    return json_data

def fix_json(json_string):
    # Load the JSON string into a Python object
    #json_obj = json.loads(json_string.replace("'", "\""))
    json_obj = json_string.replace("'", "\"")

    # Define a recursive function to process the object
    def process(obj):
        if isinstance(obj, dict):
            # If the object is a dictionary, process each key-value pair
            return {str(key): process(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            # If the object is a list, process each element
            return [process(element) for element in obj]
        else:
            # If the object is neither a dictionary nor a list, return it as is
            return obj

    # Process the object and dump it back into a JSON string
    fixed_json = json.dumps(process(json_obj))

    return fixed_json

print (fix_json("{\"reasoning\":'Hello! I am a text-based AI, so I don't have feelings or emotions', \"command\":{\"name\":'answer', \"input\":'I am a text-based AI, so I don't have feelings or emotions'}}"))

print (json.loads(fix_json("{\"reasoning\":'Hello! I am a text-based AI, so I don't have feelings or emotions', \"command\":{\"name\":'answer', \"input\":'I am a text-based AI, so I don't have feelings or emotions'}}")))

j = json.loads(fix_json("{\"reasoning\":'Hello! I am a text-based AI, so I don't have feelings or emotions', \"command\":{\"name\":'answer', \"input\":'I am a text-based AI, so I don't have feelings or emotions'}}"))
print(type(j))
d = eval(j)
print (d['reasoning'])
