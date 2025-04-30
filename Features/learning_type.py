import streamlit as st
from utils import get_user_learning_type, set_learning_type

def display_learning_type(user_id):
    st.title("Discover Your Learning Type - VARK Questionnaire")
    
    current_type = get_user_learning_type(user_id)
    if current_type:
        st.success(f"Your current learning type: {current_type}")
        st.write("Want to retake the quiz? Use the form below.")
    
    st.subheader("The VARK Questionnaire (Version 7.8)")
    st.write("How Do I Learn Best?")
    
    # Clearer instructions about being able to select multiple answers
    st.info("""
    Instructions:
    - Choose the answer(s) which best explain your preference for each question.
    - You can select more than one option if a single answer does not match your perception.
    - Select all that apply to you - there's no limit on how many you can choose per question.
    """)
    
    with st.form("vark_questionnaire"):
        all_answers = {}
        
        # Question 1
        st.write("1. You are helping someone who wants to go to your airport, the center of town or railway station. You would:")
        q1_options = [
            "go with her.",
            "tell her the directions.",
            "write down the directions.",
            "draw, or show her a map, or give her a map."
        ]
        q1_selections = []
        for i, option in enumerate(q1_options):
            if st.checkbox(option, key=f"q1_{i}"):
                q1_selections.append(chr(97 + i))  # Convert to a, b, c, d
        all_answers[1] = q1_selections
        
        # Question 2
        st.write("2. A website has a video showing how to make a special graph. There is a person speaking, some lists and words describing what to do and some diagrams. You would learn most from:")
        q2_options = [
            "seeing the diagrams.",
            "listening.",
            "reading the words.",
            "watching the actions."
        ]
        q2_selections = []
        for i, option in enumerate(q2_options):
            if st.checkbox(option, key=f"q2_{i}"):
                q2_selections.append(chr(97 + i))
        all_answers[2] = q2_selections
        
        # Question 3
        st.write("3. You are planning a vacation for a group. You want some feedback from them about the plan. You would:")
        q3_options = [
            "describe some of the highlights they will experience.",
            "use a map to show them the places.",
            "give them a copy of the printed itinerary.",
            "phone, text or email them."
        ]
        q3_selections = []
        for i, option in enumerate(q3_options):
            if st.checkbox(option, key=f"q3_{i}"):
                q3_selections.append(chr(97 + i))
        all_answers[3] = q3_selections
        
        # Question 4
        st.write("4. You are going to cook something as a special treat. You would:")
        q4_options = [
            "cook something you know without the need for instructions.",
            "ask friends for suggestions.",
            "look on the Internet or in some cookbooks for ideas from the pictures.",
            "use a good recipe."
        ]
        q4_selections = []
        for i, option in enumerate(q4_options):
            if st.checkbox(option, key=f"q4_{i}"):
                q4_selections.append(chr(97 + i))
        all_answers[4] = q4_selections
        
        # Question 5
        st.write("5. A group of tourists want to learn about the parks or wildlife reserves in your area. You would:")
        q5_options = [
            "talk about, or arrange a talk for them about parks or wildlife reserves.",
            "show them maps and internet pictures.",
            "take them to a park or wildlife reserve and walk with them.",
            "give them a book or pamphlets about the parks or wildlife reserves."
        ]
        q5_selections = []
        for i, option in enumerate(q5_options):
            if st.checkbox(option, key=f"q5_{i}"):
                q5_selections.append(chr(97 + i))
        all_answers[5] = q5_selections
        
        # Question 6
        st.write("6. You are about to purchase a digital camera or mobile phone. Other than price, what would most influence your decision?")
        q6_options = [
            "Trying or testing it.",
            "Reading the details or checking its features online.",
            "It is a modern design and looks good.",
            "The salesperson telling me about its features."
        ]
        q6_selections = []
        for i, option in enumerate(q6_options):
            if st.checkbox(option, key=f"q6_{i}"):
                q6_selections.append(chr(97 + i))
        all_answers[6] = q6_selections
        
        # Question 7
        st.write("7. Remember a time when you learned how to do something new. Avoid choosing a physical skill, e.g. riding a bike. You learned best by:")
        q7_options = [
            "watching a demonstration.",
            "listening to somebody explaining it and asking questions.",
            "diagrams, maps, and charts - visual clues.",
            "written instructions – e.g. a manual or book."
        ]
        q7_selections = []
        for i, option in enumerate(q7_options):
            if st.checkbox(option, key=f"q7_{i}"):
                q7_selections.append(chr(97 + i))
        all_answers[7] = q7_selections
        
        # Question 8
        st.write("8. You have a problem with your heart. You would prefer that the doctor:")
        q8_options = [
            "gave you a something to read to explain what was wrong.",
            "used a plastic model to show what was wrong.",
            "described what was wrong.",
            "showed you a diagram of what was wrong."
        ]
        q8_selections = []
        for i, option in enumerate(q8_options):
            if st.checkbox(option, key=f"q8_{i}"):
                q8_selections.append(chr(97 + i))
        all_answers[8] = q8_selections
        
        # Question 9
        st.write("9. You want to learn a new program, skill or game on a computer. You would:")
        q9_options = [
            "read the written instructions that came with the program.",
            "talk with people who know about the program.",
            "use the controls or keyboard.",
            "follow the diagrams in the book that came with it."
        ]
        q9_selections = []
        for i, option in enumerate(q9_options):
            if st.checkbox(option, key=f"q9_{i}"):
                q9_selections.append(chr(97 + i))
        all_answers[9] = q9_selections
        
        # Question 10
        st.write("10. I like websites that have:")
        q10_options = [
            "things I can click on, shift or try.",
            "interesting design and visual features.",
            "interesting written descriptions, lists and explanations.",
            "audio channels where I can hear music, radio programs or interviews."
        ]
        q10_selections = []
        for i, option in enumerate(q10_options):
            if st.checkbox(option, key=f"q10_{i}"):
                q10_selections.append(chr(97 + i))
        all_answers[10] = q10_selections
        
        # Question 11
        st.write("11. Other than price, what would most influence your decision to buy a new non-fiction book?")
        q11_options = [
            "The way it looks is appealing.",
            "Quickly reading parts of it.",
            "A friend talks about it and recommends it.",
            "It has real-life stories, experiences and examples."
        ]
        q11_selections = []
        for i, option in enumerate(q11_options):
            if st.checkbox(option, key=f"q11_{i}"):
                q11_selections.append(chr(97 + i))
        all_answers[11] = q11_selections
        
        # Question 12
        st.write("12. You are using a book, CD or website to learn how to take photos with your new digital camera. You would like to have:")
        q12_options = [
            "a chance to ask questions and talk about the camera and its features.",
            "clear written instructions with lists and bullet points about what to do.",
            "diagrams showing the camera and what each part does.",
            "many examples of good and poor photos and how to improve them."
        ]
        q12_selections = []
        for i, option in enumerate(q12_options):
            if st.checkbox(option, key=f"q12_{i}"):
                q12_selections.append(chr(97 + i))
        all_answers[12] = q12_selections
        
        # Question 13
        st.write("13. Do you prefer a teacher or a presenter who uses:")
        q13_options = [
            "demonstrations, models or practical sessions.",
            "question and answer, talk, group discussion, or guest speakers.",
            "handouts, books, or readings.",
            "diagrams, charts or graphs."
        ]
        q13_selections = []
        for i, option in enumerate(q13_options):
            if st.checkbox(option, key=f"q13_{i}"):
                q13_selections.append(chr(97 + i))
        all_answers[13] = q13_selections
        
        # Question 14
        st.write("14. You have finished a competition or test and would like some feedback. You would like to have feedback:")
        q14_options = [
            "using examples from what you have done.",
            "using a written description of your results.",
            "from somebody who talks it through with you.",
            "using graphs showing what you had achieved."
        ]
        q14_selections = []
        for i, option in enumerate(q14_options):
            if st.checkbox(option, key=f"q14_{i}"):
                q14_selections.append(chr(97 + i))
        all_answers[14] = q14_selections
        
        # Question 15
        st.write("15. You are going to choose food at a restaurant or cafe. You would:")
        q15_options = [
            "choose something that you have had there before.",
            "listen to the waiter or ask friends to recommend choices.",
            "choose from the descriptions in the menu.",
            "look at what others are eating or look at pictures of each dish."
        ]
        q15_selections = []
        for i, option in enumerate(q15_options):
            if st.checkbox(option, key=f"q15_{i}"):
                q15_selections.append(chr(97 + i))
        all_answers[15] = q15_selections
        
        # Question 16
        st.write("16. You have to make an important speech at a conference or special occasion. You would:")
        q16_options = [
            "make diagrams or get graphs to help explain things.",
            "write a few key words and practice saying your speech over and over.",
            "write out your speech and learn from reading it over several times.",
            "gather many examples and stories to make the talk real and practical."
        ]
        q16_selections = []
        for i, option in enumerate(q16_options):
            if st.checkbox(option, key=f"q16_{i}"):
                q16_selections.append(chr(97 + i))
        all_answers[16] = q16_selections
        
        submitted = st.form_submit_button("Submit Questionnaire")
        
        if submitted:
            # VARK Scoring Chart
            vark_chart = {
                1: {"a": "K", "b": "A", "c": "R", "d": "V"},
                2: {"a": "V", "b": "A", "c": "R", "d": "K"},
                3: {"a": "K", "b": "V", "c": "R", "d": "A"},
                4: {"a": "K", "b": "A", "c": "V", "d": "R"},
                5: {"a": "A", "b": "V", "c": "K", "d": "R"},
                6: {"a": "K", "b": "R", "c": "V", "d": "A"},
                7: {"a": "K", "b": "A", "c": "V", "d": "R"},
                8: {"a": "R", "b": "K", "c": "A", "d": "V"},
                9: {"a": "R", "b": "A", "c": "K", "d": "V"},
                10: {"a": "K", "b": "V", "c": "R", "d": "A"},
                11: {"a": "V", "b": "R", "c": "A", "d": "K"},
                12: {"a": "A", "b": "R", "c": "V", "d": "K"},
                13: {"a": "K", "b": "A", "c": "R", "d": "V"},
                14: {"a": "K", "b": "R", "c": "A", "d": "V"},
                15: {"a": "K", "b": "A", "c": "R", "d": "V"},
                16: {"a": "V", "b": "A", "c": "R", "d": "K"}
            }
            
            # Calculate VARK scores
            v_score = 0
            a_score = 0
            r_score = 0
            k_score = 0
            
            # Count the VARK scores based on the answers
            for question_num, answers in all_answers.items():
                for answer in answers:
                    if answer in vark_chart[question_num]:
                        vark_type = vark_chart[question_num][answer]
                        if vark_type == "V":
                            v_score += 1
                        elif vark_type == "A":
                            a_score += 1
                        elif vark_type == "R":
                            r_score += 1
                        elif vark_type == "K":
                            k_score += 1
            
            # Display scores
            st.subheader("Your VARK Learning Style Results")
            
            scores_df = {
                "Visual": v_score,
                "Aural/Auditory": a_score,
                "Read/Write": r_score,
                "Kinesthetic": k_score
            }
            
            # Create a bar chart
            st.bar_chart(scores_df)
            
            # Find the dominant learning style(s)
            max_score = max(v_score, a_score, r_score, k_score)
            dominant_styles = []
            
            if v_score == max_score:
                dominant_styles.append("Visual")
            if a_score == max_score:
                dominant_styles.append("Aural/Auditory")
            if r_score == max_score:
                dominant_styles.append("Read/Write")
            if k_score == max_score:
                dominant_styles.append("Kinesthetic")
            
            # Display results
            st.write(f"Visual (V): {v_score}")
            st.write(f"Aural/Auditory (A): {a_score}")
            st.write(f"Read/Write (R): {r_score}")
            st.write(f"Kinesthetic (K): {k_score}")
            
            # Determine if it's a single or multimodal preference
            learning_type = ""
            if len(dominant_styles) == 1:
                learning_type = dominant_styles[0]
                st.success(f"Your dominant learning style is: {learning_type}")
            else:
                learning_type = "Multimodal (" + ", ".join(dominant_styles) + ")"
                st.success(f"You have a multimodal learning preference: {learning_type}")
            
            # Save the learning type
            if set_learning_type(user_id, learning_type):
                st.session_state.learning_type_completed = True
                st.info("Based on your learning type, we'll customize your study experience.")
            else:
                st.error("There was an error saving your learning type. Please try again.")
    
    # Place the button outside the form
    if st.session_state.get("learning_type_completed", False):
        if st.button("Continue to Dashboard"):
            st.rerun()  # This will trigger a rerun and go to dashboard