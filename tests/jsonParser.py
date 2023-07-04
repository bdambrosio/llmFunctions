import json
import re
import traceback
from alphawave.JSONResponseValidator import JSONResponseValidator

def is_json_like(s):
    s = s.strip()
    return s.startswith('{') and s.endswith('}')

def convert_json_like_to_dict(s):
    try:
        validator = JSONResponseValidator()
        sd = {"message":s}
        json_str = validator.validate_response(None, None, None, response, 1)
        print(f'JSONResponseValidator Success! {json_str}')
        return sd["message"]
    except Exception as e:
        print (' fail in string eval', s, e)
        return s

def convert_dict_values_to_dict(d):
    for k, v in d.items():
        if isinstance(v, str) and is_json_like(v):
            d[k] = convert_json_like_to_dict(v)
    return d

def parse_to_json(input_str):
    print(f'***** ptj {input_str}')
    # Convert the string to dictionary
    if type(input_str) == dict:
        return input_str
    input_dict = convert_json_like_to_dict(input_str)
    
    # Convert the values of the dictionary to dictionary if they are JSON-like
    input_dict = convert_dict_values_to_dict(input_dict)
    
    # Convert the dictionary to JSON
    json_str = json.dumps(input_dict)
    
    return json_str


def find_json_like_string(text):
    # Regular expression to match a string that starts with '{', ends with '}', and contains balanced curly braces
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx >=0 and end_idx >= start_idx:
        return text[start_idx:end_idx+1]
    return text

def extract_and_convert_json(text):
    text = find_json_like_string(text)
    if len(text) > 0:
        json  = parse_to_json(text)
        return json
    else: return None


if __name__ == '__main__':
    schema = {
    "type": "object",
    "properties": {
        "thoughts": {
            "type": "object",
            "properties": {
                "thought": {"type": "string"},
                "reasoning": {"type": "string"},
                "plan": {"type": "string"}
            },
            "required": ["thought", "reasoning", "plan"]
        },
        "command": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "input": {"type": "object"}
            },
            "required": ["name"]
        }
    },
    "required": ["thoughts", "command"]
    }
    validator = JSONResponseValidator(schema)
    input_str = '{"thoughts":{"thought":"The user has chosen to start from Act 1, Scene 1. I need to set the scene and introduce the characters.", "reasoning": "This will help the user understand what is happening in the story and who are involved.", "plan": "- use narrate command to describe the setting- introduce the three witches"},"command": {"name":"narrate", "input":{"scene":"Act 1, Scene 1",",setting":"A heath near Forres, Scotland.","description":"Thunder and lightning. Enter three Witches.First Witch:When shall we three meet again?In thunder, lightning, or in rain?Second Witch:When the hurly-burly\'s done,When the battles lost and won.Third Witch:That will be ere the set of sun.Enter Macbeth."}}}'

    #input_str = '{  "thoughts": {    "thought": "The user has chosen to start from Act 1, Scene 1. I need to set the scene and introduce the characters.",    "reasoning": "This will help the user understand what is happening in the story and who are involved.",    "plan": "- use narrate command to describe the setting\\n- introduce the three witches"  },  "command": {    "name":"narrate",    "input":{      "scene":"Act 1, Scene 1",      "setting":"A heath near Forres, Scotland.",      "description":"Thunder and lightning. Enter three Witches.\\n\\nFirst Witch:\\nWhen shall we three meet again?\\nIn thunder, lightning, or in rain?\\n\\nSecond Witch:\\nWhen the hurly-burly"s done,\\nWhen the battle"s lost and won.\\n\\nThird Witch:\\nThat will be ere the set of sun.\\nEnter Macbeth."     }   }}'
    response = {"message":{"content":input_str}}
    print(type(input_str), type(response), type(response['message']))
    
    try:
        json_str = validator.validate_response(None, None, None, response, 1)
        print(f"JSONResponseValidator {json_str['valid']}! {json_str}")
    except:
        print('\nJSONResponseValidator fail',json_str)
    #try:
    #    json_str = extract_and_convert_json(input_str)
    #    print(json_str)
    #except:
    #    traceback.print_exc()
    #    print ('err parse', input_str)
    """
    input_str = '{"sentiment": "positive", "sentiment":  "positive"}'
    response = {"message":input_str}
    try:
        json_str = validator.validate_response(None, None, None, response, 1)
        print(f'JSONResponseValidator Success! {json_str}')
    except:
        print('\nJSONResponseValidator fail')
    try:
        json_str = extract_and_convert_json(input_str)
        print(json_str)
    except:
        #traceback.print_exc()
        print ('err parse', input_str)


    input_str = "{\"sentiment\": \"positive\"}', 'sentiment':  'positive'}"
    try:
        json_str = validator.validate(input_str)
        print(json_str)
    except:
        print('JSONResponseValidator fail\n')
    try:
        json_str = parse_to_json(input_str)
        print(json_str)
    except:
        #traceback.print_exc()
        print ('err parse', input_str)

    input_str = "{\"sentiment\": \"positive\"}', 'sentiment':  'positive'}"
    try:
        json_str = validator.validate(input_str)
        print(json_str)
    except:
        print('JSONResponseValidator fail\n')
    try:
        json_str = parse_to_json(input_str)
        print(json_str)
    except:
        #traceback.print_exc()
        print ('err parse', input_str)


    input_str = "{'answer': 'Sure, here is a valid JSON object: {\"sentiment\": \"positive\"}', 'sentiment':  'positive'}"
    try:
        json_str = extract_and_convert_json(input_str)
        print(json_str)
    except Exception as e:
        traceback.print_exc()
        print ('err extract', str(e), input_str)

    input_str = {'role': 'assistant', 'content': '{\'answer\':"Great to hear!", \'sentiment\':    \'positive\'}'}
    try:
        json_str = parse_to_json(input_str)
        print(json_str)
    except:
        print ('err', input_str)

    input_str = {'role': 'assistant', 'content': "{'answer':'Great to  hear!','sentiment':'positive'}"}
    try:
        json_str = parse_to_json(input_str)
        print(json_str)
    except:
        print('err',input_str)

    input_str = {'answer': 'I am happy too!', 'sentiment':  'positive'}
    try:
        json_str = parse_to_json(input_str.replace("'", "\""))
        print(json_str)
    except:
        print('err', input_str)

    input_str = "some random text before {'answer': 'Sure, here is a valid JSON object: {\"sentiment\": \"positive\"}', 'sentiment':  'positive'}"
    try:
        json_str = parse_to_json(input_str)
        print(json_str)
    except:
        print ('err', input_str)

    input_str = {'role': 'assistant', 'content': '{\'answer\':"Great to hear!", \'sentiment\':    \'positive\'}'}
    try:
        json_str = parse_to_json(input_str)
        print(json_str)
    except:
        print ('err', input_str)

    input_str = {'role': 'assistant', 'content': "{'answer':'Great to  hear!','sentiment':'positive'}"}
    try:
        json_str = parse_to_json(input_str)
        print(json_str)
    except:
        print('err',input_str)

"""
