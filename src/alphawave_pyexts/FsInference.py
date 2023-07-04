import socket
import string
import gc
import sys
import json
from collections.abc import Iterable
import traceback

import torch
import accelerate
from threading import Event
from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaTokenizer, TextIteratorStreamer
from transformers.generation.logits_process import (
    LogitsProcessorList,
    RepetitionPenaltyLogitsProcessor,
    TemperatureLogitsWarper,
    TopKLogitsWarper,
    TopPLogitsWarper,
)


#from fastchat.conversation import get_conv_template, SeparatorStyle
#from fastchat.model.model_adapter import load_model, get_conversation_template
#from fastchat.model.chatglm_model import chatglm_generate_stream
#from fastchat.model.falcon_model import falcon_generate_stream
#from fastchat.modules.gptq import GptqConfig
#from fastchat.utils import is_partial_stop


def prepare_logits_processor(
    temperature: float, repetition_penalty: float, top_p: float, top_k: int
) -> LogitsProcessorList:
    processor_list = LogitsProcessorList()
    # TemperatureLogitsWarper doesn't accept 0.0, 1.0 makes it a no-op so we skip two cases.
    if temperature >= 1e-5 and temperature != 1.0:
        processor_list.append(TemperatureLogitsWarper(temperature))
    if repetition_penalty > 1.0:
        processor_list.append(RepetitionPenaltyLogitsProcessor(repetition_penalty))
    if 1e-8 <= top_p < 1.0:
        processor_list.append(TopPLogitsWarper(top_p))
    if top_k > 0:
        processor_list.append(TopKLogitsWarper(top_k))
    return processor_list


def infer(model, tokenizer, prompt, temperature=0.2, top_p=1.0, context_len=2048, max_new_tokens=50, stop_str=None, echo=False, stop_token_ids = []):
    device = torch.cuda.current_device()
    input_ids = tokenizer(prompt).input_ids
    output_ids = list(input_ids)
    past_key_values = out = None
    len_prompt = len(prompt)
    repetition_penalty = 1.0
    top_k = 50
    stop_token_ids.append(tokenizer.eos_token_id)
    stream_interval = 2
    max_src_len = context_len - max_new_tokens - 8
    input_ids = input_ids[-max_src_len:]
    input_echo_len = len(input_ids)
    
    logits_processor = prepare_logits_processor(
        temperature, repetition_penalty, top_p, top_k
    )

    print(f'max new tokens {max_new_tokens}')
    for i in range(max_new_tokens):
        print(i)
        if i == 0:
            out = model(torch.as_tensor([input_ids], device=device), use_cache=True)
        else:
           try:
               out = model(
                input_ids=torch.as_tensor([[token]], device=device),
                use_cache=True,
                past_key_values=past_key_values,
               )
           except Exception as e:
               print(str(e))
               traceback.print_exc()
        logits = out.logits
        past_key_values = out.past_key_values
        last_token_logits = logits[0, -1, :]
        
        probs = torch.softmax(last_token_logits, dim=-1)
        token = int(torch.multinomial(probs, num_samples=1))

        output_ids.append(token)

        if token in stop_token_ids:
            stopped = True
        else:
            stopped = False

        if i % stream_interval == 0 or i == max_new_tokens - 1 or stopped:
            if echo:
                tmp_output_ids = output_ids
                rfind_start = len_prompt
            else:
                tmp_output_ids = output_ids[input_echo_len:]
                rfind_start = 0

            output = tokenizer.decode(
                tmp_output_ids,
                skip_special_tokens=True,
                spaces_between_special_tokens=False,
            )

            partially_stopped = False
            if stop_str:
                if isinstance(stop_str, str):
                    pos = output.rfind(stop_str, rfind_start)
                    if pos != -1:
                        output = output[:pos]
                        stopped = True
                    else:
                        partially_stopped = is_partial_stop(output, stop_str)

                elif isinstance(stop_str, Iterable):
                    for each_stop in stop_str:
                        pos = output.rfind(each_stop, rfind_start)
                        if pos != -1:
                            output = output[:pos]
                            stopped = True
                            break
                        else:
                            partially_stopped = is_partial_stop(output, each_stop)
                            if partially_stopped:
                                break
                else:
                    print('Value Error')
                    raise ValueError("Invalid stop field type.")

            # prevent yielding partial stop sequence
            if not partially_stopped:
                print(' stream')
                yield {
                    "text": output,
                    "usage": {
                        "prompt_tokens": input_echo_len,
                        "completion_tokens": i,
                        "total_tokens": input_echo_len + i,
                    },
                    "finish_reason": None,
                }

        if stopped:
            break

# finish stream event, which contains finish reason
    if i == max_new_tokens - 1:
        finish_reason = "length"
    elif stopped:
        finish_reason = "stop"
    else:
        finish_reason = None
    print(f'finish {finish_reason}')
    yield {
        "text": output,
        "usage": {
            "prompt_tokens": input_echo_len,
            "completion_tokens": i,
            "total_tokens": input_echo_len + i,
        },
        "finish_reason": finish_reason,
    }

    # clean
    del past_key_values, out
    gc.collect()
    torch.cuda.empty_cache()


    
def submit(message, model=None, tokenizer=None, pipeline=None, stop_event=None,conn=None, stop_str = None):
    message_j = json.loads(message)
    temp = 0.7
    if 'temp' in message_j.keys():
        temp = message_j['temp']
    top_p = 1.0
    if 'top_p' in message_j.keys():
        top_p = message_j['top_p']
    max_tokens = 100
    if 'max_tokens' in message_j.keys():
        max_tokens = message_j['max_tokens']
    user_prompt = 'User'
    if 'user' in message_j.keys():
        user_prompt = message_j['user']
    asst_prompt = 'Assistant'
    if 'asst' in message_j.keys():
        asst_prompt = message_j['asst']
    eos = '<|endoftext|>'
    if 'eos' in message_j.keys():
        eos = message_j['eos']
    prompt = message_j['prompt']
    
    print(f'\n temp {temp}, top_p: {top_p}, max_tokens={max_tokens}\n')

    result_stream = infer(model, tokenizer, prompt, temp, top_p, max_new_tokens=max_tokens, stop_token_ids=[eos])
    generated_text = ''
    for chunk in result_stream:
        new_text = chunk['text']
        print(new_text)
        test_text = generated_text + new_text
        idx1 = test_text.find('<|endoftext|>')
        idx2 = test_text.find(user_prompt)
        idx3 = -1
        if stop_str is not None and isinstance(stop_str, Iterable):
          for stop in stop_str:
            idx3 = max(idx3, test_text.find(stop))
        if stop_event.is_set(): # flush generate
          continue
        if idx1>= 0 or idx2>=0 or idx3 >= 0:
          stop_event.set()
          idx = min(max(idx1, 0), max(idx2,0), max(idx3,0))
          if idx > 0:
            conn.send(bytearray((new_text[:idx]).encode('utf8')))
            print(f'set stop event in submit {idx1}, {idx2}, {idx3}')
        else:
          generated_text = test_text
          conn.send(bytearray((new_text).encode('utf8')))  # send data to the client
    return generated_text



def server(model=None, tokenizer=None, pipeline=None, stop_str=None):
    # either model/tokenizer OR pipeline.
    # stop_str is a list of stop_strings
    # get the hostname
    host = socket.gethostname()
    host = ''
    port = 5004  # initiate port no above 1024
    stop_event = Event()
    print(f"starting server {stop_str}")
    while True:
      try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM)  as server_socket: # get instance
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))  # bind host address and port together
            server_socket.settimeout(3)

            while True:
                try:
                    conn = None
                    server_socket.listen(10)
                    #print("waiting...")
                    try:
                      conn, address = server_socket.accept()  # accept new connection
                    except Exception:
                      pass
                    if conn is None: continue
                    print("Connection from: " + str(address))
                    query_string = ''
                    while True:
                      s = conn.recv(1024)
                      if s is None or not s:
                        break
                      if (len(s) > 5 and s[-3:] == b'xff' and s[-6:-3] == b'x00'):
                        s = s[:-6]
                        query_string += s.decode('utf-8')
                        break
                      else:
                        query_string += s.decode('utf-8')
                    print("got string:", query_string)
                    if query_string is not None and len(query_string) > 0:
                        message_j = json.loads(query_string)
                        submit(query_string, model=model, tokenizer=tokenizer, pipeline=pipeline, stop_event=stop_event, conn=conn, stop_str=stop_str)
                        print('sending termination')
                        conn.sendall(b'x00xff')
                    if conn is not None: conn.close()
                except TimeoutError:
                  #traceback.print_exc()
                  if conn is not None: conn.close()
                except KeyboardInterrupt:
                  print("idle loop interrrupt")
                  traceback.print_exc()
                  sys.exit(0)
        print("resetting socket")
        server_socket.close()
      except BrokenPipeError:
        pass
      except KeyboardInterrupt:
        sys.exit(0)
      except Exception:
        traceback.print_exc()


























if __name__ == '__main__':
    model_name = "JosephusCheung/Guanaco"

    print('devices', torch.cuda.device_count(), torch.cuda.current_device())
    print(f"Starting to load the model {model_name} into memory")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
    )
    model.tie_weights()

    prev_text_len = 0
    while True:
        prompt = input('?')
        for value in infer(model, tokenizer, device, prompt):
            text=value['text']
            text = "".join(filter(lambda x: x in string.printable, text))
            print(value['text'][prev_text_len:])
            prev_text_len = len(value['text'])
            if value['finish_reason'] is not None:
                print(value['finish_reason'])
                break
