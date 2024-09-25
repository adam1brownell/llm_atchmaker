import streamlit as st
import numpy as np
import time
import random
import os
import sys
from rag import EMBED_MODEL, retrieve, retrieve_full_profiles

st.set_page_config(layout="wide")

TEST_QUERY = "I want to date someone who is smart, funny, and honest. I like to hike and scream at the moon."
K = 3

ai_intro_message1 = """
Hello! I am an AI Matchmaker. I'm hoping that after a few basic questions,
                 and a little back-and-forth,
                 we can find a few good matches for you!
"""
ai_intro_message2 = """
To start, what's your name?
"""
ai_intro_message3 = """
Now, tell me a little about yourself! Feel free to brag a little. Also fill out the Data Filters in the side bar when you have a chance
"""
ai_intro_message4 = """
Great, thanks for sharing. And what are you looking for in a romantic partner?
"""

ai_intro_message5 = """
Understood. Let me think if I want to ask any follow up questions...
"""

ai_intro_message6 = """
Let me look for some dating profiles...
"""

ai_intro_message7 = """
OK! Here are a few profiles that may be interesting to you, and why I think you may like them (🟢). Please review them and give them a score so I know how close/far off I am from finding a good match.
"""

okc_prompts =[
    "What are you excited about in your life?",
    "What are you really good at?",
    "What is the first thing people usually notice about you?",
    "What are your favorite books, movies, show, music, and food?",
    "What are the six things you couldn't live without?",
    "What does your ideal/typical Friday night look like?",
    "What do your friends like the most about you?",
    "What hobbies do you enjoy?",
    "What's the most important trait you value in a relationship?",
    "Tell me about your past relationships.",
    "What are your long-term goals?",
    "How do you handle conflict in relationships?"
]

def response_generator(response): 
    for word in response.split():
        yield word + " "
        time.sleep(0.1)

def score_color(progress):
    # Red -> Green color gradient (0 -> 255 for green, 255 -> 0 for red)
    red = int(255 * (1 - progress / 100))
    green = int(255 * (progress / 100))
    return f"rgb({red}, {green}, 0)"

def main():
    st.title("AI Matchmaker")


    if 'messages' not in st.session_state:
        # State Update
        st.session_state.messages = []
        st.session_state.name_flag = False
        st.session_state.name_str = ""
        st.session_state.about_me_flag = False
        st.session_state.about_me_str = ""
        st.session_state.looking_for_flag = False
        st.session_state.looking_for_str = ""
        st.session_state.enough_info = False
        st.session_state.seen_profiles = False

        st.session_state.profile_score = [None for i in range(K)]
        st.session_state.profile_show_slider = [False for i in range(K)]


        # Movie
        with st.chat_message("AI"):
            st.write_stream(response_generator(ai_intro_message1))
            time.sleep(0.75)
            st.write_stream(response_generator(ai_intro_message2))

        # Cache
        st.session_state.messages.append({"role": "AI", "content": ai_intro_message1})
        st.session_state.messages.append({"role": "AI", "content": ai_intro_message2})

        st.rerun()

    if len(st.session_state.messages) > 0:
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"],unsafe_allow_html=True)

    # SIDE BAR INFO
    # Only revealed after name turn
    if st.session_state.name_flag:
        st.sidebar.title("Dating Filters")
        st.session_state.sex = None
        st.session_state.sex_preference = None

        st.session_state.sex = st.sidebar.selectbox(
            'You are',
            ['Male', 'Female', None]
        )
        st.session_state.sex_preference = st.sidebar.selectbox(
            'Looking for',
            ['Male', 'Female', None]
        )

        # Add a slider in the sidebar
        st.session_state.age_range = st.sidebar.slider(
            'Age Range',
            18, 100, (25, 45)
        )

        st.sidebar.image("data/robot_matchmaker.jpg")


    ### TURNS START ###

    # Name Turn
    if not st.session_state.name_flag:
        if name := st.chat_input("Enter your name"):
            
            # State Update
            st.session_state.name_flag = True
            st.session_state.name_str = name

            # Movie
            with st.chat_message(name):
                st.markdown(st.session_state.name_str)
            with st.chat_message("AI"):
                st.write_stream(response_generator(f"Nice to meet you {st.session_state.name_str}."))
                time.sleep(0.75)
                st.write_stream(response_generator(ai_intro_message3))

            # Cache
            st.session_state.messages.append({"role": "user", "content": st.session_state.name_str})
            st.session_state.messages.append({"role": "AI", "content": f"Nice to meet you, {st.session_state.name_str}."})
            st.session_state.messages.append({"role": "AI", "content": ai_intro_message3})

            st.rerun()
    
    # About Turn
    elif not st.session_state.about_me_flag:
        if about := st.chat_input("Talk About yourself"):
            
            # State update
            st.session_state.about_me_flag = True
            st.session_state.about_me_str = about

            # Movie
            with st.chat_message(st.session_state.name_str):
                st.markdown(st.session_state.about_me_str)
            with st.chat_message("AI"):
                st.write_stream(response_generator(ai_intro_message4))

            # Cache
            st.session_state.messages.append({"role": "user", "content": st.session_state.about_me_str})
            st.session_state.messages.append({"role": "AI", "content":ai_intro_message4})

            st.rerun()

    # partner Turn
    elif not st.session_state.looking_for_flag:
        if partner := st.chat_input("Describe your ideal partner"):
            
            # State update
            st.session_state.looking_for_flag = True
            st.session_state.looking_for_str = partner

            # Movie
            with st.chat_message(st.session_state.name_str):
                st.markdown(st.session_state.looking_for_str)
            with st.chat_message("AI"):
                st.write_stream(response_generator(ai_intro_message5))
                time.sleep(1)
                okc_q = random.choice(okc_prompts)
                st.write_stream(response_generator(okc_q))

            # Cache
            st.session_state.messages.append({"role": "user", "content": st.session_state.looking_for_str})
            st.session_state.messages.append({"role": "AI", "content":ai_intro_message5})
            st.session_state.messages.append({"role": "AI", "content":okc_q})

            st.rerun()

    # Could be a while loop but this refreshed every interaction
    # so no need for the loop!
    elif not st.session_state.enough_info:

        # User can either input their response or press skip
        col1, col2 = st.columns([10, 1])

        user_input = col1.chat_input("Type your message here...")

        # Capture skip button
        skip_button = col2.button("Skip") 
        
        if user_input:

            # State Update
            # TODO: LLM to decide if it has enough info (OR check RAG for score?)

            # Movie
            with st.chat_message(st.session_state.name_str):
                st.markdown(user_input)
            with st.chat_message("AI"):
                st.write_stream(response_generator(ai_intro_message5))
                time.sleep(1)
                okc_q = random.choice(okc_prompts)
                st.write_stream(response_generator(okc_q))

            # Cache
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "AI", "content":ai_intro_message5})
            st.session_state.messages.append({"role": "AI", "content":okc_q})

            st.rerun()


        elif skip_button:

            # State Update
            st.session_state.enough_info = True

            # Movie
            with st.chat_message("AI"):
                st.write_stream(response_generator(ai_intro_message6))
                time.sleep(2)
                st.write_stream(response_generator(ai_intro_message7))
            
            # Cache
            st.session_state.messages.append({"role": "user", "content": "{Skip Button}"})
            st.session_state.messages.append({"role": "AI", "content": ai_intro_message6})
            st.session_state.messages.append({"role": "AI", "content":ai_intro_message7})
        
            st.rerun()

    elif not st.session_state.seen_profiles:
    # if not st.session_state.seen_profiles:

        top_p_ids, top_chunks, similarity_scores = retrieve(TEST_QUERY,k=K)
        stats,essays = retrieve_full_profiles(top_p_ids)

        columns = st.columns([1 for i in range(K)])

        for i in range(K):
            col = columns[i]
            p_stats = stats.loc[stats.p_id==top_p_ids[i]].reset_index(drop=True)
            p_essays = essays.loc[essays.p_id==top_p_ids[i]]
            chunk = top_chunks[i]
            with col:
                st.title(f"Profile #{top_p_ids[i]}")
                st.image("data/blank_pfp.png")
                if (st.session_state.profile_score[i] is not None) and (st.session_state.profile_score[i] != 50):
                    score = st.session_state.profile_score[i]
                    score_str = f"Score: {score}/100"
                    st.markdown(f"""
                                <style>
                                .stProgress .st-bo {{
                                    background-color: {score_color(score)};
                                }}
                                </style>
                                """, unsafe_allow_html=True)
                    score_str = f"Score: {st.session_state.profile_score[i]}/100"
                    st.progress(st.session_state.profile_score[i],text=score_str)
                
                st.dataframe(p_stats,use_container_width=True)
                for q in p_essays.columns:
                    if q == 'p_id':
                        continue
                    answer = p_essays[q].values[0]
                    if isinstance(answer, str):
                        exp_txt = f'{q}'
                        if (chunk in answer) or (answer in chunk):
                            exp_txt = "🟢 "+exp_txt
                        with st.expander(exp_txt):
                            if chunk in answer:
                                spltr = answer.split(chunk)
                                txt = f'<p style="background-color:rgba(34, 139, 34, 0.3); color:white; padding:1px">{spltr[0]+chunk+spltr[1]}</p>'
                            elif answer in chunk:
                                txt = f'<p style="background-color:rgba(34, 139, 34, 0.3); color:white; padding:1px">{answer}</p>'
                            else:
                                txt = f'<p>{answer}</p>'
                            st.markdown(txt, unsafe_allow_html=True)

                st.write(top_chunks[i])

                if st.button(f"Rate Profile",key=f"rate_{i}"):
                    st.session_state.profile_show_slider[i] = True
                
                if st.session_state.profile_show_slider[i] == True:
                    slider_val = st.slider(f"Select score for {col}", 1, 100,
                                                                  value=50, key=f"slider_{i}")
                    if slider_val != 50:
                        st.session_state.profile_score[i] = slider_val
                        st.session_state.profile_show_slider[i] = False

        if st.button(f"Done"):

            # State Update
            st.session_state.seen_profiles = True

            tmp_s = "Great, thanks for taking a look and giving some scores. Let me take a moment to review..."
            # Movie
            with st.chat_message("AI"):
                st.write_stream(response_generator(tmp_s))
            
            # Cache
            st.session_state.messages.append({"role": "AI", "content": tmp_s})
            st.session_state.messages.append({"role": "AI", "content": "Goodbye"})
        
            st.rerun()
if __name__ == "__main__":
    main()