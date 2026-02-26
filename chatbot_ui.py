import streamlit as st
from chatbot_backend import chatbot, retrieve_all_threads
from createDBTITLES import update_title, get_title, insert_chat_title

from langchain.messages import HumanMessage, AIMessage, ToolMessage
import uuid

#***************utiliy function*****************
def generate_thread_id():
    thread_id= uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state.thread_id = thread_id
    st.session_state.messages = []
    add_thread(thread_id)
    insert_chat_title(thread_id,'New Chat..')

def add_thread(thread_id):
    if thread_id not in st.session_state.chat_threads:
        st.session_state.chat_threads.append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )

    # No graph run yet → empty conversation
    if not state.values or 'messages' not in state.values:
        return []

    return state.values['messages']
#**************** SESSION SETUP ******************


if 'chat_threads' not in st.session_state:
    st.session_state.chat_threads = retrieve_all_threads()


if 'thread_id' not in st.session_state:
    thread_id= generate_thread_id()
    st.session_state.thread_id = thread_id
    add_thread(thread_id)
    insert_chat_title(thread_id,'New Chat...')


print(get_title(st.session_state.thread_id))

config = {'configurable': {'thread_id': st.session_state.thread_id}}

if 'messages' not in st.session_state:
    st.session_state.messages=[]



#*********************** SIDEBAR UI ****************************************
st.sidebar.title('LangGraph Chatbot')
if st.sidebar.button('New Chat'):
    reset_chat()
st.sidebar.header('My Conversation')

for thread_id in st.session_state.chat_threads[::-1]:
    if st.sidebar.button(get_title(thread_id),key=f"chat_{thread_id}"):
        st.session_state['thread_id']= thread_id
        conversation=load_conversation(thread_id)

        temp_messages = []

        for message in conversation:
            if isinstance(message, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role': role, 'message': message.content})
        st.session_state.messages = temp_messages

#*********************** MAIN UI *************************************************

for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.write(msg['message'])

# user_query = st.chat_input("Your Message")

# if user_query: this can also be written as



if user_query := st.chat_input("Your Message"):
    with st.chat_message('user'):
        st.session_state.messages.append({'role':'user', 'message':user_query})
        st.write(user_query)

        short_title = user_query[:30] + "..." if len(user_query)>30 else user_query
        update_title(st.session_state.thread_id, short_title)
    
    with st.chat_message('assistant'):
        initial_state = {
            'messages': [HumanMessage(content=user_query)]
        }
        
        status = st.status("Thinking...", expanded=True)

        def stream_with_status():
            for message_chunk, _ in chatbot.stream(
                initial_state,
                config=config,
                stream_mode='messages'
            ):
                if isinstance(message_chunk, AIMessage):
                    if message_chunk.tool_calls:
                        for tool_call in message_chunk.tool_calls:
                            status.update(
                                label=f"🔧 Using tool: {tool_call['name']}",
                                state = 'running'
                            )
                
                    content = message_chunk.content
                    if isinstance(content, list):
                        for block in content:
                            if block.get('type')=='text':
                                yield block.get('text')
                    elif isinstance(content, str):
                        yield content
                elif isinstance(message_chunk, ToolMessage):
                    status.update(
                        label=f'✅ Tool `{message_chunk.name}` completed',
                        state ='complete'
                    )
                
            

        response = st.write_stream(stream_with_status())
        status.update(state = 'complete')

        st.session_state.messages.append({'role':'assistant', 'message': response})