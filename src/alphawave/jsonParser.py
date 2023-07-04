import json
import re

def parse_json_value(value):
    try:
        # Attempt to parse the value as JSON
        return json.loads(value)
    except json.JSONDecodeError:
        # If parsing fails, return the original value
        return value

def parse_to_json(input_str):
    # Convert the string to dictionary
    input_dict = json.loads(input_str, object_hook=lambda d: {k: parse_json_value(v) if isinstance(v, str) else v for k, v in d.items()})
    
    # Convert the dictionary to JSON
    json_str = json.dumps(input_dict)
    
    return json_str

if __name__ == '__main__':
    input_str = "{'answer': 'Sure, here is a valid JSON object: {\"sentiment\": \"positive\"}', 'sentiment':  'positive'}"
json_str = parse_to_json(input_str.replace("'", "\""))
print(json_str)
