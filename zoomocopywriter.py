import streamlit as st
import requests
import uuid # For generating session IDs

# --- CONFIGURATION ---
# !!! REPLACE WITH YOUR ACTUAL N8N WEBHOOK URL !!!
N8N_WEBHOOK_URL = "https://ridezoomo.app.n8n.cloud/webhook/conversational-copy"
# --- END CONFIGURATION ---

# Set page config first (must be the first Streamlit command)
st.set_page_config(
    page_title="Zoomo's Copywriter",
    page_icon="🤖",
    layout="wide"
)

# Apply custom CSS for Zoomo branding
with open("style.css") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize chat history and session ID in session_state
if "messages" not in st.session_state:
    st.session_state.messages = [] # To store all messages {role: "user/assistant", content: "..."}
if "sessionId" not in st.session_state:
    st.session_state.sessionId = str(uuid.uuid4()) # Generate a unique session ID for this browser session

st.title("🤖 Zoomo's Copywriter")

# Add description and guidance
st.markdown("""
Hey there! I'm here to help you craft effective copy matching Zoomo's voice and brand guidelines. For best results, please include these details when requesting copy:

- Target audience: Leads, Customers, Former Customers
- Market(s): UK, ES, DE, AU, US, CA, FR, Global
- Objective: Nurture, Onboarding, Promotion, Operational, Announcement, etc.
- Language: English, Spanish, German, French, Arabic
- Channel: Email, SMS, WhatsApp, Push Notification, Web Copy, Social Media, etc
- Optional: Desired length, key points to include, specific tone
""")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("How can I help with your Zoomo copy today?"):
    # Add user message to session state and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare data for n8n
    # Send the conversation history *before* adding the current user's prompt
    # This way, n8n gets the history leading up to the latest input.
    history_for_n8n = [msg for msg in st.session_state.messages[:-1]]


    payload = {
        "currentUserInput": prompt,
        "conversationHistory": history_for_n8n, 
        "sessionId": st.session_state.sessionId
    }

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # For "typing" effect
        full_response_text = ""
        try:
            # Send request to n8n
            response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=90) # Increased timeout for potentially long LLM calls
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            
            n8n_response_data = response.json()
            
            assistant_reply = n8n_response_data.get("assistantResponse", "Sorry, I received an unexpected response format from the agent.")
            
            # Simulate stream of response (optional, for better UX)
            # For a real stream, you'd use a streaming response from n8n if possible.
            # This is a simple character-by-character display.
            # for char in assistant_reply:
            #     full_response_text += char
            #     message_placeholder.markdown(full_response_text + "▌")
            #     time.sleep(0.02) # Adjust speed
            message_placeholder.markdown(assistant_reply) # Display full response at once
            full_response_text = assistant_reply # Store the full response

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response_text})

        except requests.exceptions.Timeout:
            st.error("The request to the AI agent timed out. Please try again.")
            full_response_text = "Sorry, the request timed out."
            message_placeholder.markdown(full_response_text)
            st.session_state.messages.append({"role": "assistant", "content": full_response_text})
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the AI agent: {e}")
            full_response_text = "Sorry, there was an issue connecting to the AI agent."
            message_placeholder.markdown(full_response_text)
            st.session_state.messages.append({"role": "assistant", "content": full_response_text})
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            full_response_text = f"An unexpected error occurred: {e}" # Show the error
            message_placeholder.markdown(full_response_text)
            st.session_state.messages.append({"role": "assistant", "content": full_response_text})
